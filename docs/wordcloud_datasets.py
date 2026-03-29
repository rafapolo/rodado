#!/usr/bin/env python3
import json
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt

with open('context/basedosdados-schema.json') as f:
    schema = json.load(f)

dataset_names = []
for dataset in schema.keys():
    parts = dataset.replace('br_', '').replace('mundo_', '').replace('eu_', '').split('_')
    dataset_names.extend([p for p in parts if len(p) >= 3])

word_freq = Counter(dataset_names)

wc = WordCloud(
    width=1600, 
    height=800, 
    background_color='white',
    max_words=100,
    colormap='plasma',
    min_font_size=10
).generate_from_frequencies(word_freq)

plt.figure(figsize=(20, 10))
plt.imshow(wc, interpolation='bilinear')
plt.axis('off')
plt.tight_layout(pad=0)
plt.savefig('docs/wordcloud_datasets.png', dpi=150, bbox_inches='tight')
print("Saved docs/wordcloud_datasets.png")
print(f"Total unique words: {len(word_freq)}")
print("Top 30:", word_freq.most_common(30))
