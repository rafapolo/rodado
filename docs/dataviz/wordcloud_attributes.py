#!/usr/bin/env python3
import json
import re
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt

STOPWORDS = {'de', 'do', 'da', 'a', 'ou', 'em', 'e', 'o', 'que', 'das', 'dos', 'nos', 'nas', 'um', 'uma', 'para', 'com', 'não', 'uma', 'à', 'ao', 'os', 'as', 'se', 'na', 'no', 'de', 'do', 'da', 'é', 'ser', 'seu', 'sua', 'isso', 'the', 'of', 'and', 'in', 'to', 'is', 'for', 'on', 'with', 'at', 'by', 'from'}

with open('context/basedosdados-schema.json') as f:
    schema = json.load(f)

words = []
for dataset, tables in schema.items():
    for table, cols in tables.items():
        for col in cols:
            name = col.get('name', '').lower()
            desc = col.get('description', '').lower()
            if name and len(name) >= 3:
                words.append(name)
            if desc:
                for w in desc.split():
                    w = re.sub(r'[^a-záàâãéèêíìîóòôõúùûç]', '', w)
                    if len(w) >= 3 and w not in STOPWORDS:
                        words.append(w)

word_freq = Counter(words)

wc = WordCloud(
    width=1600, 
    height=800, 
    background_color='white',
    max_words=200,
    colormap='viridis',
    min_font_size=8
).generate_from_frequencies(word_freq)

plt.figure(figsize=(20, 10))
plt.imshow(wc, interpolation='bilinear')
plt.axis('off')
plt.tight_layout(pad=0)
plt.savefig('docs/wordcloud_attributes.png', dpi=150, bbox_inches='tight')
print("Saved docs/wordcloud_attributes.png")
print(f"Total unique words: {len(word_freq)}")
print("Top 30:", word_freq.most_common(30))
