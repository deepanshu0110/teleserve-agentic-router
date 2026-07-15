from transformers import AutoModelForSequenceClassification, AutoTokenizer
m = AutoModelForSequenceClassification.from_pretrained("teleserve_merged_215")
t = AutoTokenizer.from_pretrained("teleserve_merged_215")
print("loaded ok, num_labels =", m.config.num_labels)