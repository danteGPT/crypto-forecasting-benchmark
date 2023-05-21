import numpy as np
import torch
from darts import TimeSeries
from darts.dataprocessing.transformers import Scaler
from darts.metrics import mape, rmse
from darts.models import NBEATSModel
from darts.datasets import AirPassengersDataset
from ray import tune
from ray.tune import CLIReporter
from ray.tune.schedulers import ASHAScheduler

# Load the data and perform scaling
series = AirPassengersDataset().load()
scaler = Scaler()
series_scaled = scaler.fit_transform(series)

# Define the search space for hyperparameters
config = {
    "input_chunk_length": tune.choice([12, 24, 36, 48]),
    "num_layers": tune.choice([1, 2, 3]),
    "num_blocks": tune.choice([3, 4, 5]),
    "layer_widths": tune.choice([10, 20, 30]),
}

# Define a scheduler to manage trial scheduling
scheduler = ASHAScheduler(
    metric="loss", mode="min", max_t=100, grace_period=1, reduction_factor=2
)


# Define the objective function to minimize
def objective(config):
    model = NBEATSModel(
        input_chunk_length=config["input_chunk_length"],
        output_chunk_length=1,  # Set to 1 for one-step-ahead forecasting
        num_blocks=int(config["num_blocks"] * config["num_layers"]),
        layer_widths=int(config["layer_widths"] * config["num_layers"]),
        n_epochs=100,
        random_state=0,
        pl_trainer_kwargs={
            "accelerator": "auto",
            "enable_progress_bar": False,
        },
    )

    # Splitting into non-overlapping training and test sets
    test_size_percentage = 0.25
    n_periods = 9
    test_size = int(len(series_scaled) / (1 / test_size_percentage - 1 + n_periods))
    train_size = int(test_size * (1 / test_size_percentage - 1))

    total_mape = 0
    total_rmse = 0
    for i in range(n_periods):
        start = i * (train_size + test_size)
        end = start + train_size

        # Initial training data
        train_ts = series_scaled[start:end]

        # Make a rolling forecast for each time step in the test period
        for t in range(test_size):
            # Train the model on the current training data
            model.fit(train_ts, verbose=True)

            # One-step-ahead forecasting
            pred = model.predict(n=1)

            # Compute the loss on the test data
            mape_loss = mape(series_scaled[end + t : end + t + 1], pred)
            rmse_loss = rmse(series_scaled[end + t : end + t + 1], pred)

            total_mape += mape_loss.mean().item()
            total_rmse += rmse_loss.mean().item()

            # Add the actual observed value to the training data
            train_ts = train_ts.append(series_scaled[end + t : end + t + 1])

    # Average test loss
    avg_mape = total_mape / n_periods
    avg_rmse = total_rmse / n_periods

    # Tune reports the metrics back to its optimization engine
    tune.report(mape=avg_mape, rmse=avg_rmse)


# Define a reporter to track progress
reporter = CLIReporter(metric_columns=["mape", "rmse", "training_iteration"])

# Use Ray Tune to perform hyperparameter tuning
tune.run(
    objective,
    resources_per_trial={"cpu": 8, "gpu": 1},
    config=config,
    num_samples=10,
    scheduler=scheduler,
    progress_reporter=reporter,
)
