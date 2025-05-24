from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)

# Define file paths
data_path = os.path.join(os.path.dirname(__file__), "dss_data_smartphones_main.csv")

# Load data
df = pd.read_csv("dss_data_smartphones_main.csv")

# Convert columns to numeric and handle missing values
for col in [
    "price",
    "avg_rating",
    "camera_sentiment_roberta",
    "battery_sentiment_roberta",
    "display_sentiment_roberta",
    "performance_sentiment_roberta",
    "build_sentiment_roberta",
    "storage_sentiment_roberta",
    "camera_mentions",
    "battery_mentions",
    "display_mentions",
    "performance_mentions",
    "build_mentions",
    "storage_mentions",
    "review_count",
]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=["price", "title", "avg_rating"])
df["value_score"] = df["avg_rating"] / df["price"]


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        price_limit = float(request.form["price_limit"])
        min_mentions = int(request.form["min_mentions"])
        priorities = request.form.getlist("priorities") or ["overall"]

        # Enforce "overall" exclusivity
        if "overall" in priorities and len(priorities) > 1:
            priorities = ["overall"]

        # Criteria mapping using RoBERTa sentiment scores
        criteria = {
            "camera": "camera_sentiment_roberta",
            "battery": "battery_sentiment_roberta",
            "display": "display_sentiment_roberta",
            "performance": "performance_sentiment_roberta",
            "build": "build_sentiment_roberta",
            "storage": "storage_sentiment_roberta",
        }

        # Compute results
        if "value" in priorities and len(priorities) == 1:
            result = (
                df[(df["price"] <= price_limit) & (df["review_count"] >= min_mentions)]
                .sort_values("value_score", ascending=False)
                .head(3)
            )
        elif "overall" in priorities:
            weights = [0.25] + [0.15] * 6
            df["composite_score"] = weights[0] * df["avg_rating"] + sum(
                weights[i + 1] * df[criteria[c]] for i, c in enumerate(criteria.keys())
            )
            result = (
                df[(df["price"] <= price_limit) & (df["review_count"] >= min_mentions)]
                .sort_values("composite_score", ascending=False)
                .head(3)
            )
        else:
            num_priorities = len(priorities)
            high_weight = 0.7 / num_priorities
            low_weight = (1.0 - high_weight * num_priorities) / (7 - num_priorities)
            weights = [0.2]
            for crit in criteria:
                weights.append(high_weight if crit in priorities else low_weight)
            df["composite_score"] = (
                weights[0] * df["avg_rating"]
                + weights[1] * df["camera_sentiment_roberta"]
                + weights[2] * df["battery_sentiment_roberta"]
                + weights[3] * df["display_sentiment_roberta"]
                + weights[4] * df["performance_sentiment_roberta"]
                + weights[5] * df["build_sentiment_roberta"]
                + weights[6] * df["storage_sentiment_roberta"]
            )
            result = (
                df[(df["price"] <= price_limit) & (df["review_count"] >= min_mentions)]
                .sort_values("composite_score", ascending=False)
                .head(3)
            )

        recommendations = result.to_dict(orient="records")
        return render_template(
            "results.html", recommendations=recommendations, priorities=priorities
        )

    return render_template("index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
