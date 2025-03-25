import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import math
import numpy as np

def load_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def extract_metrics(entry, metrics, i):
    extracted_metrics = {}
    print(f"extract_metrics - entry['browserScripts'][{i}]")
    print(f"entry['browserScripts'][i]: {entry['browserScripts'][i]}")
    for metric in metrics:
        metric_name, expression = metric
        try:
            print(f"metric_name: {metric_name}, i: {i}, expression {expression}")
            if metric_name == "MeanTRRFirstSentToLastReceived":
                trr_first_sent = entry['geckoPerfStats'][i]['TRRFirstSentToLastReceived']
                trr_request_count = entry['geckoPerfStats'][i]['TRRRequestCount']
                if trr_request_count != 0:
                    value = trr_first_sent / trr_request_count
                else:
                    value = None
                    print(f"TRRRequestCount is zero for entry {i}. Setting MeanTRRFirstSentToLastReceived to None.")
            else:
                value = eval(expression)
            print(f"value: {value}")
            extracted_metrics[metric_name] = value
        except (KeyError, IndexError, TypeError, ZeroDivisionError) as e:
            extracted_metrics[metric_name] = None
            print(f"metric_name: {metric_name}, none!, i: {i}")
            print(f"Error: {e}")
    return extracted_metrics

def main(directory_path, plot_type='violin', output_dir='plots'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    metrics_to_parse = [
        ["document_dns_lookup", "entry['geckoPerfStats'][i]['document_dns_lookup']"],
        ["connectStart", "entry['browserScripts'][i]['timings']['navigationTiming']['connectStart']"],
        ["trr_lookup_time", "entry['geckoPerfStats'][i]['trr_lookup_time'] / entry['geckoPerfStats'][i]['trr_service_channel_count']"],        
        ["trr_service_channel_count", "entry['geckoPerfStats'][i]['trr_service_channel_count']"],
        ["trr_dns_start", "entry['geckoPerfStats'][i]['trr_dns_start'] / entry['geckoPerfStats'][i]['trr_service_channel_count']"],
        ["trr_dns_end", "entry['geckoPerfStats'][i]['trr_dns_end'] / entry['geckoPerfStats'][i]['trr_service_channel_count']"],
        ["trr_tcp_connection", "entry['geckoPerfStats'][i]['trr_tcp_connection'] / entry['geckoPerfStats'][i]['trr_service_channel_count']"],
        ["trr_tls_handshake", "entry['geckoPerfStats'][i]['trr_tls_handshake'] / entry['geckoPerfStats'][i]['trr_service_channel_count']"],
        ["trr_open_to_first_sent", "entry['geckoPerfStats'][i]['trr_open_to_first_sent'] / entry['geckoPerfStats'][i]['trr_service_channel_count']"],
        ["trr_first_sent_to_last_received", "entry['geckoPerfStats'][i]['trr_first_sent_to_last_received'] / entry['geckoPerfStats'][i]['trr_service_channel_count']"],
        ["trr_open_to_first_received", "entry['geckoPerfStats'][i]['trr_open_to_first_received'] / entry['geckoPerfStats'][i]['trr_service_channel_count']"],
        ["trr_complete_load", "entry['geckoPerfStats'][i]['trr_complete_load'] / entry['geckoPerfStats'][i]['trr_service_channel_count']"],
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
                    for i in range(len(entry.get('browserScripts', []))):
                        metrics = extract_metrics(entry, metrics_to_parse, i)
                        for metric in metrics_to_parse:
                            value = metrics.get(metric[0])
                            df = pd.concat([df, pd.DataFrame({
                                'Website': website_name, 
                                'Variant': os.path.basename(root), 
                                'Metric': metric[0], 
                                'Value': value
                            }, index=[0])], ignore_index=True)

    websites = df['Website'].unique()
    overall_means = df.groupby(['Variant', 'Metric'])['Value'].mean()
    overall_medians = df.groupby(['Variant', 'Metric'])['Value'].median()
    overall_counts = df.groupby(['Variant', 'Metric'])['Value'].count()

    # Plot per website
    for website in websites:
        website_df = df[df['Website'] == website]
        metrics = website_df['Metric'].unique()
        num_metrics = len(metrics)
        
        cols = math.ceil(math.sqrt(num_metrics))
        rows = math.ceil(num_metrics / cols)
        fig, axs = plt.subplots(rows, cols, figsize=(cols * 5, rows * 5))
        fig.suptitle(f"Website: {website}", fontsize=16)
        axs = axs.flatten() if num_metrics > 1 else [axs]

        for i, metric in enumerate(metrics):
            metric_df = website_df[website_df['Metric'] == metric]
            variant_groups = metric_df.groupby('Variant')
            axs[i].set_title(metric, fontsize=12)
            axs[i].set_xlabel('Variant', fontsize=10)
            axs[i].set_ylabel('Value (ms)', fontsize=10)

            if plot_type == 'scatter':
                for variant, data in variant_groups:
                    axs[i].scatter([variant] * len(data), data['Value'], label=variant)
                axs[i].tick_params(axis='x', rotation=45, labelsize=8)
            elif plot_type == 'violin':
                groups = list(variant_groups)
                violin_data = []
                for (_, group_df) in groups:
                    # Convert group values to a list then to a numpy array
                    values = group_df['Value'].dropna().tolist()
                    if not values:
                        values = [np.nan]
                    violin_data.append(np.array(values))
                labels = [variant for (variant, _) in groups]
                parts = axs[i].violinplot(violin_data, showmeans=False, showmedians=False, showextrema=False)
                axs[i].set_xticks(range(1, len(labels)+1))
                axs[i].set_xticklabels(labels, rotation=45, fontsize=8)
                for j, (variant, group_df) in enumerate(groups):
                    data = group_df['Value'].dropna()
                    if not data.empty:
                        median_val = data.median()
                        axs[i].text(j+1, median_val, f"Median: {median_val:.2f}\n",
                                    ha='center', va='bottom', color='red', fontsize=8)
            else:  # fallback to box plot
                box_data = [group[1]['Value'].dropna() for group in variant_groups]
                labels = [group[0] for group in variant_groups]
                boxplot = axs[i].boxplot(box_data, labels=labels)
                axs[i].tick_params(axis='x', rotation=45, labelsize=8)
                medians = [median_line.get_ydata()[0] for median_line in boxplot['medians']]
                for x, median_val in enumerate(medians, start=1):
                    axs[i].text(x, median_val + 0.1, f"{median_val:.2f}", 
                                ha='center', va='bottom', color='red', fontsize=8)

            means = metric_df.groupby('Variant')['Value'].mean()
            medians = metric_df.groupby('Variant')['Value'].median()
            mins = metric_df.groupby('Variant')['Value'].min()
            maxs = metric_df.groupby('Variant')['Value'].max()
            stds = metric_df.groupby('Variant')['Value'].std()
            counts = metric_df.groupby('Variant')['Value'].count()
            
            first_variant_mean = means.iloc[0] if not means.empty else None
            first_variant_median = medians.iloc[0] if not medians.empty else None

            print(f"Statistics for {metric} - {website}:")
            for variant in means.index:
                mean_diff_percent = ((means[variant] - first_variant_mean) / first_variant_mean * 100) if first_variant_mean else 0
                median_diff_percent = ((medians[variant] - first_variant_median) / first_variant_median * 100) if first_variant_median else 0
                print(f"  Variant: {variant}, Mean: {means[variant]}, Median: {medians[variant]}, Count: {counts[variant]}, Min: {mins[variant]}, Max: {maxs[variant]}, Std: {stds[variant]}")
                print(f"  Mean Delta from First Variant: {mean_diff_percent:.2f}%, Median Delta from First Variant: {median_diff_percent:.2f}%")

        for j in range(i + 1, len(axs)):
            fig.delaxes(axs[j])
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        safe_website_name = website.replace('/', '_').replace('\\', '_')
        filename = os.path.join(output_dir, f"{safe_website_name}_{plot_type}.png")
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Saved plot to {filename}")
        plt.show()

    print("\nOverall Summary:")
    num_metrics = len(metrics_to_parse)
    cols = math.ceil(math.sqrt(num_metrics))
    rows = math.ceil(num_metrics / cols)
    overall_fig, overall_axs = plt.subplots(rows, cols, figsize=(cols * 5, rows * 5))
    overall_fig.suptitle("Overall Metrics", fontsize=16)
    overall_axs = overall_axs.flatten() if num_metrics > 1 else [overall_axs]

    for i, metric in enumerate(metrics_to_parse):
        metric_name = metric[0]
        variant_groups = df[df['Metric'] == metric_name].groupby('Variant')
        overall_axs[i].set_title(metric_name, fontsize=12)
        overall_axs[i].set_xlabel('Variant', fontsize=10)
        overall_axs[i].set_ylabel('Value (ms)', fontsize=10)

        if plot_type == 'scatter':
            for variant, data in variant_groups:
                overall_axs[i].scatter([variant] * len(data), data['Value'], label=variant)
            overall_axs[i].tick_params(axis='x', rotation=45, labelsize=8)
        elif plot_type == 'violin':
            groups = list(variant_groups)
            violin_data = []
            for (_, group_df) in groups:
                values = group_df['Value'].dropna().tolist()
                if not values:
                    values = [np.nan]
                violin_data.append(np.array(values))
            labels = [variant for (variant, _) in groups]
            parts = overall_axs[i].violinplot(violin_data, showmeans=False, showmedians=False, showextrema=False)
            overall_axs[i].set_xticks(range(1, len(labels)+1))
            overall_axs[i].set_xticklabels(labels, rotation=45, fontsize=8)
            for j, (variant, group_df) in enumerate(groups):
                data = group_df['Value'].dropna()
                if not data.empty:
                    median_val = data.median()
                    overall_axs[i].text(j+1, median_val, f"Median: {median_val:.2f}\n",
                                       ha='center', va='bottom', color='red', fontsize=8)
        else:
            box_data = [group[1]['Value'].dropna() for group in variant_groups]
            labels = [group[0] for group in variant_groups]
            if box_data:
                boxplot = overall_axs[i].boxplot(box_data, labels=labels)
                overall_axs[i].tick_params(axis='x', rotation=45, labelsize=8)
                medians = [median_line.get_ydata()[0] for median_line in boxplot['medians']]
                for x, median_val in enumerate(medians, start=1):
                    overall_axs[i].text(x, median_val + 0.1, f"{median_val:.2f}",
                                        ha='center', va='bottom', color='red', fontsize=8)
            else:
                print(f"No data available to plot for metric '{metric_name}'.")

    for j in range(i + 1, len(overall_axs)):
        overall_fig.delaxes(overall_axs[j])
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    overall_filename = os.path.join(output_dir, f"overall_metrics_{plot_type}.png")
    plt.savefig(overall_filename, dpi=300, bbox_inches='tight')
    print(f"Saved overall plot to {overall_filename}")
    plt.show()

    overall_first_variant_mean = overall_means.iloc[0] if not overall_means.empty else None
    overall_first_variant_median = overall_medians.iloc[0] if not overall_medians.empty else None
    for (variant, metric), mean in overall_means.items():
        median = overall_medians.get((variant, metric), None)
        count = overall_counts.get((variant, metric), 0)
        mean_diff_percent = ((mean - overall_first_variant_mean) / overall_first_variant_mean * 100) if overall_first_variant_mean else 0
        median_diff_percent = ((median - overall_first_variant_median) / overall_first_variant_median * 100) if overall_first_variant_median else 0
        print(f"  Variant: {variant}, Metric: {metric}, Mean: {mean}, Median: {median}, Count: {count}")
        print(f"  Mean Delta from First Variant: {mean_diff_percent:.2f}%, Median Delta from First Variant: {median_diff_percent:.2f}%")

if __name__ == "__main__":
    import sys
    if len(sys.argv) not in (2, 3):
        print("Usage: python script.py <directory_path> [plot_type]")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    plot_type = sys.argv[2] if len(sys.argv) == 3 else 'violin'
    
    if plot_type and plot_type not in ('scatter', 'box', 'violin'):
        print("Invalid plot type. Use 'scatter', 'box', or 'violin' (optional)")
        sys.exit(1)
    
    main(directory_path, plot_type=plot_type)
