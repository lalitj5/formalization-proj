import os

def build_data():
    base = os.path.join("datasets", "textbook_algo")
    data_pairs = {}

    topics = sorted(t for t in os.listdir(base) if os.path.isdir(os.path.join(base, t)))
    for i, topic in enumerate(topics):
        topic_path = os.path.join(base, topic)
        spec_file = os.path.join(topic_path, f"{topic}_spec.txt")
        code_file = os.path.join(topic_path, f"{topic}_strong.dfy")
        with open(spec_file, "r") as f:
            spec = f.read().strip()
        with open(code_file, "r") as f:
            strong_dfy = f.read().strip()

        data_pairs[str(i)] = {"name": topic, "spec": spec, "strong_dfy": strong_dfy}

    return data_pairs
