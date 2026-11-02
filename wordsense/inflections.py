"""Offline spelling aliases; explicit dictionary entries always take priority.

English spelling is not a complete verb dictionary. These rules cover regular
forms and a small common irregular list, not grammar or automatic translation.
"""

IRREGULAR = {
    "be": ("was", "were", "been", "being"), "go": ("went", "gone", "going"),
    "do": ("did", "done", "doing"), "have": ("had", "having"),
    "run": ("ran", "running"), "get": ("got", "gotten", "getting"),
    "make": ("made", "making"), "take": ("took", "taken", "taking"),
    "write": ("wrote", "written", "writing"), "read": ("read", "reading"),
    "eat": ("ate", "eaten", "eating"), "see": ("saw", "seen", "seeing"),
    "come": ("came", "coming"), "give": ("gave", "given", "giving"),
    "speak": ("spoke", "spoken", "speaking"), "think": ("thought", "thinking"),
    "buy": ("bought", "buying"), "bring": ("brought", "bringing"),
    "teach": ("taught", "teaching"), "catch": ("caught", "catching"),
    "find": ("found", "finding"), "feel": ("felt", "feeling"),
    "know": ("knew", "known", "knowing"), "leave": ("left", "leaving"),
    "say": ("said", "saying"), "tell": ("told", "telling"),
    "sleep": ("slept", "sleeping"), "keep": ("kept", "keeping"),
    "sit": ("sat", "sitting"), "swim": ("swam", "swum", "swimming"),
    "begin": ("began", "begun", "beginning"), "win": ("won", "winning"),
    "put": ("put", "putting"), "cut": ("cut", "cutting"),
    "lie": ("lay", "lain", "lying"), "die": ("died", "dying"),
    "tie": ("tied", "tying"), "understand": ("understood", "understanding"),
}
DOUBLE = set("stop plan shop drop hop jog rub grab clap slip skip trip chat admit prefer refer occur regret commit permit control travel cancel".split())


def forms(word):
    if word in IRREGULAR:
        return set(IRREGULAR[word])
    if len(word) < 2 or not word.isascii() or not word.isalpha():
        return set()
    if word.endswith("e"):
        return {word + "d", (word if word.endswith(("ee", "ye", "oe")) else word[:-1]) + "ing"}
    if word.endswith("y") and word[-2] not in "aeiou":
        return {word[:-1] + "ied", word + "ing"}
    if word.endswith("c"):
        return {word + "ked", word + "king"}
    if word in DOUBLE:
        result = {word + word[-1] + "ed", word + word[-1] + "ing"}
        if word in {"travel", "cancel"}:
            result.update({word + "ed", word + "ing"})
        return result
    return {word + "ed", word + "ing"}


def build_aliases(words):
    candidates = {}
    for base in words:
        for form in forms(base):
            if form not in words:
                candidates.setdefault(form, set()).add(base)
    # Never silently choose between two possible recorded roots.
    return {form: next(iter(bases)) for form, bases in candidates.items() if len(bases) == 1}
