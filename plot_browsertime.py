import os
import json
import pandas as pd
import matplotlib.pyplot as plt

# Collects perfstats from browsertime.json
# Ensure that your comparisons match this folder structure style
# ├── twitter.com_rihanna
# │   ├── baseline
# │   │   ├── browsertime.json
# │   ├── baseline_run2
# │   │   ├── browsertime.json
# │   ├── dns_prefetch
# │   │   ├── browsertime.json
# │   └── dns_prefetch_run2
# │       ├── browsertime.json
# │                   └── data
# ├── www.amazon.ca_s_k=laptop_crid=340B5V12VLWVX_sprefix=laptop%2Caps%2C90_ref=nb_sb_noss_1
# │   ├── baseline
# │   │   ├── browsertime.json
# │   ├── baseline_run2
# │   ├── dns_prefetch
# │   │   ├── browsertime.json
# │   └── dns_prefetch_run2
# │       ├── browsertime.json
 

def load_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def extract_metrics(entry, metrics, i):
    extracted_metrics = {}
    for metric in metrics:
        metric_name, expression = metric
        try:
            #print( "metric_name: " + metric_name)
            extracted_metrics[metric_name] = eval(expression)
        except (KeyError, IndexError):
            extracted_metrics[metric_name] = None
    return extracted_metrics

def main(directory_path, plot_type='box'):

    # define the perfstats that you're interested in
    metrics_to_parse = [
        ["AsyncOpenToConnectEnd", "entry['geckoPerfStats'][i]['AsyncOpenToConnectEnd']"],
        ["AsyncOpenToFirstSent", "entry['geckoPerfStats'][i]['AsyncOpenToFirstSent']"],
        # ["HttpSubItemDnsTime", "entry['geckoPerfStats'][i]['HttpSubItemDnsTime']"],
        # ["DNSLookupCacheHit", "entry['geckoPerfStats'][i]['DNSLookupCacheHit']"],
        # ["DNSLookupNetworkFirst", "entry['geckoPerfStats'][i]['DNSLookupNetworkFirst']"],
        # ["DNSLookupNetworkShared", "entry['geckoPerfStats'][i]['DNSLookupNetworkShared']"]
    ]

    df = pd.DataFrame(columns=['Website', 'Variant', 'Metric', 'Value'])

    for root, _, filenames in os.walk(directory_path):
        website_name = os.path.basename(os.path.dirname(root))

        for filename in filenames:
            if filename.endswith('.json'):
                file_path = os.path.join(root, filename)
                data = load_json(file_path)
                print("file: " + file_path)
                for entry in data:
                    for i in range(len(entry['geckoPerfStats'])):
                        metrics = extract_metrics(entry, metrics_to_parse, i)
                        for metric in metrics_to_parse:
                            value = metrics[metric[0]]
                            df = pd.concat([df, pd.DataFrame({'Website': website_name, 'Variant': os.path.basename(root), 'Metric': metric[0], 'Value': value}, index=[0])], ignore_index=True)

    websites = df['Website'].unique()

    overall_means = df.groupby(['Variant', 'Metric'])['Value'].mean()
    overall_medians = df.groupby(['Variant', 'Metric'])['Value'].median()
    overall_counts = df.groupby(['Variant', 'Metric'])['Value'].count()

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

            if plot_type == 'scatter':
                print("scatter")
                for variant, data in variant_groups:
                    axs[i].scatter([variant] * len(data), data['Value'], label=variant)
                    axs[i].tick_params(axis='x', rotation=90)  # Rotate x-axis labels vertically
            else: 
                print("box")
                axs[i].boxplot([group[1]['Value'] for group in variant_groups], labels=[group[0] for group in variant_groups])
                axs[i].tick_params(axis='x', rotation=90)  # Rotate x-axis labels vertically
                axs[i].legend()

            # Logging statistics
            means = metric_df.groupby('Variant')['Value'].mean()
            medians = metric_df.groupby('Variant')['Value'].median()
            mins = metric_df.groupby('Variant')['Value'].min()
            maxs = metric_df.groupby('Variant')['Value'].max()
            stds = metric_df.groupby('Variant')['Value'].std()
            counts = metric_df.groupby('Variant')['Value'].count()
            
            first_variant_mean = means.iloc[0]
            first_variant_median = medians.iloc[0]

            print(f"Statistics for {metric} - {website}:")
            for variant in means.index:
                mean_diff_percent = ((means[variant] - first_variant_mean) / first_variant_mean) * 100
                median_diff_percent = ((medians[variant] - first_variant_median) / first_variant_median) * 100
                print(f"  Variant: {variant}, Mean: {means[variant]}, Median: {medians[variant]}, Count: {counts[variant]}, Min: {mins[variant]}, Max: {maxs[variant]}, Std: {stds[variant]}")
                print(f"  Mean Delta from First Variant: {mean_diff_percent:.2f}%, Median Delta from First Variant: {median_diff_percent:.2f}%")
                
        plt.tight_layout()
        plt.show()


    # Overall statistics
    print("\nOverall Summary:")
    overall_first_variant_mean = overall_means.iloc[0]
    overall_first_variant_median = overall_medians.iloc[0]

    for variant, metric in overall_means.index:
        mean_diff_percent = ((overall_means[variant, metric] - overall_first_variant_mean) / overall_first_variant_mean) * 100
        median_diff_percent = ((overall_medians[variant, metric] - overall_first_variant_median) / overall_first_variant_median) * 100
        print(f"  Variant: {variant}, Metric: {metric}, Mean: {overall_means[variant, metric]}, Median: {overall_medians[variant, metric]}, Count: {overall_counts[variant, metric]}")
        print(f"  Mean Delta from First Variant: {mean_diff_percent:.2f}%, Median Delta from First Variant: {median_diff_percent:.2f}%")
        
    print("\nOverall Summary:")
    overall_fig, overall_axs = plt.subplots(1, num_metrics, figsize=(15, 5))
    overall_fig.suptitle("Overall Metrics")

    for i, metric in enumerate(metrics):
        variant_groups = df[df['Metric'] == metric].groupby('Variant')
        overall_axs[i].set_title(metric)
        overall_axs[i].set_xlabel('Variant')
        overall_axs[i].set_ylabel('Value')

        if plot_type == 'scatter':
            for variant, data in variant_groups:
                overall_axs[i].scatter([variant] * len(data), data['Value'], label=variant)
                overall_axs[i].tick_params(axis='x', rotation=90)
        else: 
            overall_axs[i].boxplot([group[1]['Value'] for group in variant_groups], labels=[group[0] for group in variant_groups])
            overall_axs[i].tick_params(axis='x', rotation=90)
            overall_axs[i].legend()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) not in (2, 3):
        print("Usage: python script.py <directory_path> [plot_type]")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    plot_type = sys.argv[2] if len(sys.argv) == 3 else None
    
    if plot_type and plot_type not in ('scatter', 'box'):
        print("Invalid plot type. Use 'scatter' or 'box' (optional)")
        sys.exit(1)
    
    if plot_type == 'scatter':
        main(directory_path, plot_type='scatter')
    else:
        main(directory_path)
