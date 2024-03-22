import os
import json
import pandas as pd
import matplotlib.pyplot as plt

def load_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def extract_metrics(entry, metrics, i):
    extracted_metrics = {}
    for metric in metrics:
        metric_name, expression = metric
        try:
            extracted_metrics[metric_name] = eval(expression)
        except (KeyError, IndexError):
            extracted_metrics[metric_name] = None
    return extracted_metrics

def main(directory_path):

    # define the perfstats that you're interested in
    metrics_to_parse = [
        ["HttpSubItemDnsTime", "entry['geckoPerfStats'][i]['HttpSubItemDnsTime']"],
        ["DNSLookupCacheHit", "entry['geckoPerfStats'][i]['DNSLookupCacheHit']"],
        ["DNSLookupNetworkFirst", "entry['geckoPerfStats'][i]['DNSLookupNetworkFirst']"],
        ["DNSLookupNetworkShared", "entry['geckoPerfStats'][i]['DNSLookupNetworkShared']"]
    ]

    df = pd.DataFrame(columns=['Website', 'Variant', 'Metric', 'Value'])

    for root, _, filenames in os.walk(directory_path):
        website_name = os.path.basename(os.path.dirname(root))

        for filename in filenames:
            if filename.endswith('.json'):
                file_path = os.path.join(root, filename)
                data = load_json(file_path)
                for entry in data:
                    for i in range(len(entry['geckoPerfStats'])):
                        metrics = extract_metrics(entry, metrics_to_parse, i)
                        for metric in metrics_to_parse:
                            value = metrics[metric[0]]
                            df = pd.concat([df, pd.DataFrame({'Website': website_name, 'Variant': os.path.basename(root), 'Metric': metric[0], 'Value': value}, index=[0])], ignore_index=True)

    websites = df['Website'].unique()
    for website in websites:
        website_df = df[df['Website'] == website]
        metrics = website_df['Metric'].unique()
        num_metrics = len(metrics)
        fig, axs = plt.subplots(1, num_metrics, figsize=(15, 5))
        fig.suptitle(f"Website: {website}")

        for i, metric in enumerate(metrics):
            metric_df = website_df[website_df['Metric'] == metric]
            variant_groups = metric_df.groupby('Variant')
            axs[i].set_title(metric)
            axs[i].set_xlabel('Variant')
            axs[i].set_ylabel('Value')
            axs[i].boxplot([group[1]['Value'] for group in variant_groups], labels=[group[0] for group in variant_groups])
            axs[i].tick_params(axis='x', rotation=90)  # Rotate x-axis labels vertically

            # Logging statistics
            means = metric_df.groupby('Variant')['Value'].mean()
            medians = metric_df.groupby('Variant')['Value'].median()
            mins = metric_df.groupby('Variant')['Value'].min()
            maxs = metric_df.groupby('Variant')['Value'].max()
            stds = metric_df.groupby('Variant')['Value'].std()
            counts = metric_df.groupby('Variant')['Value'].count()
   
            print(f"Statistics for {metric} - {website}:")
            for variant in means.index:
                print(f"  Variant: {variant}, Mean: {means[variant]}, Median: {medians[variant]}, Count: {counts[variant]}, Min: {mins[variant]}, Max: {maxs[variant]}, Std: {stds[variant]}")
                
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory_path>")
        sys.exit(1)
    directory_path = sys.argv[1]
    main(directory_path)
