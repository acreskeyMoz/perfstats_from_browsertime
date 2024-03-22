# perfstats_from_browsertime
Tooling to extract and plot perfstats from comparative browsertime runs

You can use the tooling [here](https://github.com/acreskeyMoz/browsertime_scripts) to generate the browsertime results.

```
Ensure that your comparisons match this folder structure style
├── twitter.com_rihanna
│   ├── baseline
│   │   ├── browsertime.json
│   ├── baseline_run2
│   │   ├── browsertime.json
│   ├── dns_prefetch
│   │   ├── browsertime.json
│   └── dns_prefetch_run2
│       ├── browsertime.json
│                   └── data
├── www.amazon.ca_s_k=laptop_crid=340B5V12VLWVX_sprefix=laptop%2Caps%2C90_ref=nb_sb_noss_1
│   ├── baseline
│   │   ├── browsertime.json
│   ├── baseline_run2
│   ├── dns_prefetch
│   │   ├── browsertime.json
│   └── dns_prefetch_run2
│       ├── browsertime.json
```

## Usage

1. Define the perfstats that you want to observe in `plot_browsertime.py`
2. Run: `python python3 plot_browsertime.py {path_to_root_of_files}`


## Output

The results will be plotted and simple statistics will be output.

<img width="1487" alt="perfstats_from_browsertime" src="https://github.com/acreskeyMoz/perfstats_from_browsertime/assets/44072237/d006b350-001b-4943-8ceb-003f3ddc7945">
