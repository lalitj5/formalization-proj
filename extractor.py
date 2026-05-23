import os

# specs = list of extracting specs from folders
# code = list of extracting code
# wrapping specs and code together into data list of tuples

base = os.path.join("datasets", "textbook_algo")
specs = []
code = []

for topic in sorted(os.listdir(base)):
    topic_path = os.path.join(base, topic)
    if not os.path.isdir(topic_path):
        continue
    spec_file = os.path.join(topic_path, f"{topic}_spec.txt")
    code_file = os.path.join(topic_path, f"{topic}_strong.dfy")
    with open(spec_file, "r") as f:
        specs.append(f.read().strip())
    with open(code_file, "r") as f:
        code.append(f.read().strip())

data = list(zip(specs, code))


data_pairs = {}

for i in range(len(data)):
    key = str(i)
    data_pairs[key] = data[i] # stores tuples

print(len(data_pairs))
print(data_pairs['23'])