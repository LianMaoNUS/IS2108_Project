import joblib
import os
import time

model_path = os.path.join(os.path.dirname(__file__), 'b2c_products_500_transactions_50k.joblib')

print("Loading rules...")
start_time = time.time()
loaded_rules = joblib.load(model_path)
load_time = time.time() - start_time
print(f"Rules loaded in {load_time:.2f} seconds")
print(f"Dataset size: {len(loaded_rules)} rules")
print(f"Columns: {list(loaded_rules.columns)}")
print(f"Memory usage: {loaded_rules.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

def get_recommendations(loaded_rules, items, metric='confidence', top_n=5):
    mask = loaded_rules['antecedents'].apply(lambda x: any(item in x for item in items))
    relevant_rules = loaded_rules[mask]
    if len(relevant_rules) == 0:
        return []
    
    sorted_rules = relevant_rules.sort_values(by=metric, ascending=False)
    
    recommendations = set()
    for _, row in sorted_rules.head(top_n * 3).iterrows(): 
        recommendations.update(row['consequents'])
    
    recommendations.difference_update(items)
    return list(recommendations)[:top_n]


# Test the optimized approach
print("="*50)
print("TESTING OPTIMIZED APPROACH:")
result = get_recommendations(loaded_rules, ['AIA-JM4T8BP6'], metric='lift', top_n=5)
print(f"Result: {result}")