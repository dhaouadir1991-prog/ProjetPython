#!/usr/bin/env python
# coding: utf-8

# In[1]:


from transformers import pipeline


# In[2]:


classifier = pipeline(
    "text-classification",
    model="unitary/unbiased-toxic-roberta",
    top_k=None
)


# In[3]:


text = "You are a disgusting human being."
scores = classifier(text)[0]

for s in scores:
    print(f"{s['label']:25s} → {s['score']:.3f}")


# In[4]:


NON_ADEQUATE = any(
    s["score"] > 0.7 and s["label"] in [
        "toxicity",
        "insult",
        "threat",
        "identity_attack"
    ]
    for s in scores
)

print("NON_ADEQUATE:", NON_ADEQUATE)


# In[5]:


get_ipython().system('jupyter nbconvert --to script exploration_model.ipynb')


# In[ ]:




