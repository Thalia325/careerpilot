from app.services.reference import load_job_graph_seed


def test_graph_seed_meets_minimum_paths():
    seed = load_job_graph_seed()["jobs"]
    qualified = [item for item in seed.values() if len(item["transitions"]) >= 2]
    assert len(qualified) >= 5

