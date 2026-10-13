"""Fixed user storage and SQLite persistence, independent of cwd."""
import os
import sqlite3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import tempfile
import hashlib
import json
from contextlib import closing


def data_directory():
    root = os.environ.get("LOCALAPPDATA")
    return Path(root) / "WordSense" if root else Path.home() / ".local" / "share" / "WordSense"


def normalize(word):
    word = word.strip()
    if not word or not word.isascii() or not word.isalpha():
        raise ValueError("单词只能包含 A–Z 和 a–z。")
    return word.casefold()


def write_markdown(path, text):
    """Replace UTF-8 Markdown atomically, preserving the previous file on error."""
    write_atomic(path, text.encode("utf-8"))


def write_atomic(path, data):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb",
                                         dir=path.parent, prefix=".wordsense-", suffix=".tmp",
                                         delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class Storage:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else data_directory()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.settings_path = self.directory / "settings.json"
        self.settings = json.loads(self.settings_path.read_text(encoding="utf-8")) if self.settings_path.exists() else {}
        self.path = Path(self.settings.get("database_path", self.directory / "wordsense.sqlite3"))
        if "database_path" in self.settings and not self.path.is_file():
            raise FileNotFoundError(f"配置的词库不存在：{self.path}。请恢复该词库文件，不会自动创建空词库。")
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY,
                word TEXT NOT NULL UNIQUE,
                meaning TEXT NOT NULL,
                level INTEGER NOT NULL CHECK(level BETWEEN 0 AND 3),
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );
            CREATE TABLE IF NOT EXISTS editor_state (
                id INTEGER PRIMARY KEY CHECK(id = 1),
                text TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        self.connection.commit()
        self._migrate_understanding_levels()
        configured = self.connection.execute("SELECT value FROM app_meta WHERE key='documents_directory'").fetchone()
        self.documents_directory = Path(configured[0]) if configured else self.directory / "documents"
        self.documents_directory.mkdir(parents=True, exist_ok=True)
        self._migrate_legacy_text()
        self.writer = ThreadPoolExecutor(max_workers=1, thread_name_prefix="wordsense-save")
        self.pending = []

    def load_words(self):
        return {word: (meaning, 2 if level == 1 else level) for word, meaning, level in
                self.connection.execute("SELECT word, meaning, level FROM words")}

    def _migrate_understanding_levels(self):
        row = self.connection.execute("SELECT value FROM app_meta WHERE key='understanding_levels'").fetchone()
        if row and row[0] == 'three-v1':
            return
        with self.connection:
            self.connection.execute("UPDATE words SET level=2 WHERE level=1")
            self.connection.execute("INSERT INTO app_meta(key,value) VALUES('understanding_levels','three-v1') "
                                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value")

    def set_database_directory(self, directory):
        """Use SQLite backup to include WAL data, verify, then switch the shared pointer."""
        target_directory = Path(directory).expanduser().resolve()
        target_directory.mkdir(parents=True, exist_ok=True)
        target = target_directory / "wordsense.sqlite3"
        old = self.path.resolve()
        if old == target:
            return self.cleanup_old_database()
        if self.settings.get("old_database") and self.cleanup_old_database():
            raise OSError("请先关闭占用旧词库的程序，并清理旧词库残留。")
        if target.exists() or any(Path(str(target) + suffix).exists() for suffix in ("-wal", "-shm")):
            raise FileExistsError(f"目标已有词库：{target}。请选择其他文件夹，现有词库不会被覆盖。")
        for future in self.pending:
            future.result()
        self.collect_finished()
        if self.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0]:
            raise OSError("词库正在被其他程序使用，请关闭其他 WordSense 窗口后重试。")
        original_hash = file_hash(old)
        expected = '\n'.join(self.connection.iterdump())
        with tempfile.NamedTemporaryFile(dir=target_directory, suffix=".sqlite3", prefix=".wordsense-", delete=False) as stream:
            staged = Path(stream.name)
        new_connection = None
        old_closed = False
        installed = False
        try:
            with closing(sqlite3.connect(staged)) as snapshot:
                self.connection.backup(snapshot)
                if snapshot.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or '\n'.join(snapshot.iterdump()) != expected:
                    raise OSError("词库备份校验失败，保留原词库。")
                snapshot.execute("PRAGMA journal_mode=DELETE")
            # The destination is owned by this migration; never replace a pre-existing DB.
            with target.open("xb") as output:
                installed = True
                output.write(staged.read_bytes())
                output.flush()
                os.fsync(output.fileno())
            new_connection = sqlite3.connect(target)
            new_connection.execute("PRAGMA journal_mode=WAL")
            self.connection.close()
            old_closed = True
            if file_hash(old) != original_hash:
                raise OSError("迁移期间原词库发生变化，已保留原词库，请关闭其他写作窗口后重试。")
            updated = dict(self.settings, database_path=str(target), old_database={"path": str(old), "hash": original_hash})
            write_atomic(self.settings_path, (json.dumps(updated, ensure_ascii=False, indent=2) + '\n').encode("utf-8"))
        except Exception:
            if new_connection is not None:
                new_connection.close()
            if old_closed:
                self.connection = sqlite3.connect(old)
                self.connection.execute("PRAGMA journal_mode=WAL")
            if installed:
                target.unlink(missing_ok=True)
            raise
        finally:
            staged.unlink(missing_ok=True)
        self.settings = updated
        self.path = target
        self.connection = new_connection
        return self.cleanup_old_database()

    def cleanup_old_database(self):
        entry = self.settings.get("old_database")
        if not entry:
            return []
        old = Path(entry['path']).resolve()
        if old == self.path.resolve() or old.name != "wordsense.sqlite3":
            raise ValueError("旧词库清理配置无效。")
        leftovers = []
        try:
            if old.exists():
                wal = Path(str(old) + "-wal")
                if old.is_symlink() or file_hash(old) != entry['hash'] or (wal.exists() and wal.stat().st_size):
                    raise OSError("旧词库已变化或仍被占用")
                old.unlink()
            for suffix in ("-wal", "-shm"):
                Path(str(old) + suffix).unlink(missing_ok=True)
        except OSError:
            leftovers.append(str(old))
        if not leftovers:
            updated = dict(self.settings)
            updated.pop("old_database", None)
            try:
                write_atomic(self.settings_path, (json.dumps(updated, ensure_ascii=False, indent=2) + '\n').encode("utf-8"))
                self.settings = updated
            except OSError:
                leftovers.append(str(self.settings_path))
        return leftovers

    def upsert_word(self, word, meaning, level):
        key = normalize(word)
        level = 2 if level == 1 else level  # Old '有点印象' entries become '有点模糊'.
        if level not in (0, 2, 3):
            raise ValueError("请选择完全理解、有点模糊或完全不懂。")
        with self.connection:
            self.connection.execute("""
                INSERT INTO words(word, meaning, level) VALUES (?, ?, ?)
                ON CONFLICT(word) DO UPDATE SET meaning=excluded.meaning,
                level=excluded.level, updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
            """, (key, meaning.strip(), level))
        return key

    def document_path(self, document_date=None):
        day = document_date or date.today()
        if isinstance(day, str):
            day = date.fromisoformat(day)
        if not isinstance(day, date):
            raise ValueError("文档日期无效")
        return self.documents_directory / f"{day.isoformat()}.md"

    def _migrate_legacy_text(self):
        migrated = self.connection.execute("SELECT value FROM app_meta WHERE key='markdown_migrated'").fetchone()
        if migrated:
            return
        row = self.connection.execute("SELECT text FROM editor_state WHERE id=1").fetchone()
        path = self.document_path()
        if row and not path.exists():
            write_markdown(path, row[0])
        with self.connection:
            self.connection.execute("INSERT INTO app_meta(key,value) VALUES('markdown_migrated','1')")

    def load_text(self, document_date=None):
        path = self.document_path(document_date)
        return path.read_text(encoding="utf-8") if path.exists() else "  "

    def set_documents_directory(self, directory):
        """Copy and verify first, commit the setting, then remove verified originals."""
        for future in self.pending:
            future.result()
        self.collect_finished()
        old = self.documents_directory.resolve()
        target = Path(directory).expanduser().resolve()
        if old == target:
            return 0, self.cleanup_old_documents()
        if target.is_relative_to(old):
            raise ValueError("新位置不能是当前文档目录的子目录。")
        if self.connection.execute("SELECT value FROM app_meta WHERE key='documents_cleanup'").fetchone():
            leftovers = self.cleanup_old_documents()
            if leftovers:
                raise OSError("请先关闭占用旧文档的程序，并清理旧位置残留后再更换目录。")
        target.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target):
            pass  # Verify that even an empty collection can be saved here.
        entries = []
        for source in sorted(old.glob("*.md")):
            try:
                if date.fromisoformat(source.stem).isoformat() != source.stem:
                    continue
            except ValueError:
                continue  # Preserve unrelated Markdown in a user-selected folder.
            if source.is_symlink() or not source.is_file():
                raise ValueError(f"无法迁移非普通文件：{source.name}")
            digest = file_hash(source)
            destination = target / source.name
            if destination.exists() and (not destination.is_file() or destination.is_symlink()
                                          or file_hash(destination) != digest):
                raise FileExistsError(f"新目录已有不同内容的同名文档：{source.name}，原文档未删除。")
            entries.append({"name": source.name, "hash": digest})
        created = []
        try:
            for entry in entries:
                source, destination = old / entry["name"], target / entry["name"]
                if not destination.exists():
                    write_atomic(destination, source.read_bytes())
                    created.append((destination, entry["hash"]))
                if file_hash(source) != entry["hash"] or file_hash(destination) != entry["hash"]:
                    raise OSError(f"文档迁移校验失败：{source.name}，原文档未删除。")
            plan = {"old": str(old), "target": str(target), "files": entries,
                    "temporary": [p.name for p in old.glob('.wordsense-*.tmp') if p.is_file() and not p.is_symlink()]}
            with self.connection:
                self.connection.execute("INSERT INTO app_meta(key,value) VALUES('documents_directory',?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(target),))
                self.connection.execute("INSERT INTO app_meta(key,value) VALUES('documents_cleanup',?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (json.dumps(plan),))
        except Exception:
            for destination, digest in created:
                try:
                    if destination.exists() and file_hash(destination) == digest:
                        destination.unlink()
                except OSError:
                    pass  # Originals and the old setting still remain authoritative.
            raise
        self.documents_directory = target
        return len(entries), self.cleanup_old_documents()

    def cleanup_old_documents(self):
        row = self.connection.execute("SELECT value FROM app_meta WHERE key='documents_cleanup'").fetchone()
        if not row:
            return []
        plan = json.loads(row[0])
        old, target = Path(plan['old']).resolve(), Path(plan['target']).resolve()
        if old == target or target != self.documents_directory.resolve():
            raise ValueError("旧文档清理配置无效。")
        remaining, temporary, leftovers = [], [], []
        for entry in plan['files']:
            source, destination = old / entry['name'], target / entry['name']
            try:
                if source.exists():
                    if source.is_symlink() or destination.is_symlink() or file_hash(source) != entry['hash'] or file_hash(destination) != entry['hash']:
                        raise OSError("文档已改变，保留原文件")
                    source.unlink()
            except OSError:
                remaining.append(entry)
                leftovers.append(str(source))
        for name in plan.get('temporary', []):
            source = old / name
            try:
                if source.is_symlink():
                    raise OSError("保留符号链接")
                source.unlink(missing_ok=True)
            except OSError:
                temporary.append(name)
                leftovers.append(str(source))
        plan.update(files=remaining, temporary=temporary)
        with self.connection:
            if leftovers:
                self.connection.execute("UPDATE app_meta SET value=? WHERE key='documents_cleanup'", (json.dumps(plan),))
            else:
                self.connection.execute("DELETE FROM app_meta WHERE key='documents_cleanup'")
        if not leftovers and old != self.directory.resolve() and old != Path(old.anchor):
            try:
                old.rmdir()  # Only remove an empty old directory; unrelated files stay.
            except OSError:
                pass
        return leftovers

    def save_text(self, text, document_date=None):
        # Capture the path now; later date changes cannot redirect a pending save.
        path = self.document_path(document_date)
        def write():
            write_markdown(path, text)
        future = self.writer.submit(write)
        self.pending.append(future)
        return future

    def collect_finished(self):
        remaining = []
        errors = []
        for future in self.pending:
            if future.done():
                try:
                    future.result()
                except Exception as error:
                    errors.append(error)
            else:
                remaining.append(future)
        self.pending = remaining
        if errors:
            raise errors[0]

    def close(self):
        self.writer.shutdown(wait=True)
        try:
            for future in self.pending:
                future.result()
        finally:
            self.connection.close()
