import streamlit as st
from PIL import Image

from telescope.filters import AVAILABLE_FILTERS, ComposedFilter
from telescope.metrics import AVAILABLE_METRICS, COMET
from telescope.metrics.metric import Metric
from telescope.plotting import (
    plot_bootstraping_result,
    plot_bucket_comparison,
    plot_pairwise_distributions,
    plot_segment_comparison,
)
from telescope.testset import PairwiseTestset
from telescope.metrics.result import PairwiseResult

available_metrics = {m.name: m for m in AVAILABLE_METRICS}
available_filters = {f.name: f for f in AVAILABLE_FILTERS if f.name != "length"}

# Text/Title
st.sidebar.title("MT-Telescope LOGO")


@st.cache
def load_image(image_file):
    img = Image.open(image_file)
    return img


# --------------------  APP Settings --------------------
metrics = st.sidebar.multiselect(
    "Select the system-level metric you wish to run:",
    list(available_metrics.keys()),
    default=["COMET", "chrF", "sacreBLEU"],
)

metric = st.sidebar.selectbox(
    "Select the segment-level metric you wish to run:",
    list(m.name for m in available_metrics.values() if m.segment_level),
    index=0,
)

filters = st.sidebar.multiselect(
    "Select testset filters:", list(available_filters.keys()), default=["duplicates"]
)
st.sidebar.subheader("Segment length constraints:")
length_interval = st.sidebar.slider(
    "Specify the confidence interval for the length distribution:",
    0,
    100,
    step=5,
    value=(0, 100),
    help=(
        "In order to isolate segments according to caracter length "
        "we will create a sequence length distribution that you can constraint "
        "through it's density funcion. This slider is used to specify the confidence interval P(a < X < b)"
    ),
)
if length_interval != (0, 100):
    filters = (
        filters
        + [
            "length",
        ]
        if filters is not None
        else [
            "length",
        ]
    )

st.sidebar.subheader("Bootstrap resampling settings:")
num_samples = st.sidebar.number_input(
    "Number of random partitions:",
    min_value=1,
    max_value=1000,
    value=300,
    step=50,
)
sample_ratio = st.sidebar.slider(
    "Proportion (P) of the initial sample:", 0.0, 1.0, value=0.5, step=0.1
)

# --------------------- Streamlit APP Caching functions! --------------------------

cache_time = 60 * 60  # 1 hour cache time for each object
cache_max_entries = 30  # 1 hour cache time for each object


def hash_metrics(metrics):
    return " ".join([m.name for m in metrics])


@st.cache(
    hash_funcs={PairwiseTestset: PairwiseTestset.hash_func},
    suppress_st_warning=True,
    show_spinner=False,
    allow_output_mutation=True,
    ttl=cache_time,
    max_entries=cache_max_entries,
)
def apply_filters(testset, filters):
    with st.spinner(f"Applying {filter} filter..."):
        filters = [available_filters[f](testset, *length_interval) for f in filters]
        composed_filter = ComposedFilter(testset, filters)
        return composed_filter.apply_filter()


@st.cache(
    hash_funcs={PairwiseTestset: PairwiseTestset.hash_func},
    show_spinner=False,
    allow_output_mutation=True,
    ttl=cache_time,
    max_entries=cache_max_entries,
)
def run_metric(testset, metric):
    metric = available_metrics[metric](language=testset.target_language)
    with st.spinner(f"Running {metric.name}..."):
        return metric.pairwise_comparison(testset)


def run_all_metrics(testset, metrics, filters):
    if filters:
        corpus_size = len(testset)
        testset = apply_filters(testset, filters)
        st.success(
            "Corpus reduced in {:.2f}%".format((1 - (len(testset) / corpus_size)) * 100)
        )
    return {metric: run_metric(testset, metric) for metric in metrics}


# --------------------  APP  --------------------

st.title("Welcome to MT-Telescope!")
testset = PairwiseTestset.read_data()

if testset:
    if metric not in metrics:
        metrics = [
            metric,
        ] + metrics
    results = run_all_metrics(testset, metrics, filters)
    if len(results) > 0:
        st.dataframe(PairwiseResult.results_to_dataframe(list(results.values())))

    if metric in results:
        if metric == "COMET":
            st.header("Error-type analysis:")
            plot_bucket_comparison(results[metric])

        st.header("Segment-level comparison:")
        plot_segment_comparison(results[metric])

        st.header("Segment-level scores histogram:")
        plot_pairwise_distributions(results[metric])

        # Bootstrap Resampling
        _, middle, _ = st.beta_columns(3)
        if middle.button("Perform Bootstrap Resampling:"):
            st.warning(
                "Running metrics for {} partitions of size {}".format(
                    num_samples, sample_ratio * len(testset)
                )
            )
            st.header("Bootstrap resampling results:")
            with st.spinner("Running bootstrap resampling..."):
                for metric in metrics:
                    bootstrap_result = available_metrics[metric].bootstrap_resampling(
                        testset, int(num_samples), sample_ratio, results[metric]
                    )

                    plot_bootstraping_result(bootstrap_result)
