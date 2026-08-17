import numpy as np
import pytest

from src.failure_memory.embedding import FailureEmbedder


def _contexts(n=20, seed=0):
    rng = np.random.default_rng(seed)
    return [{"a": float(rng.normal()), "b": float(rng.normal()), "c": float(rng.normal())} for _ in range(n)]


def test_embed_before_fit_raises():
    embedder = FailureEmbedder(["a", "b", "c"], n_components=2)
    with pytest.raises(RuntimeError):
        embedder.embed({"a": 1.0, "b": 1.0, "c": 1.0}, confidence=0.5)


def test_output_dim_is_pca_components_plus_two():
    embedder = FailureEmbedder(["a", "b", "c"], n_components=2).fit(_contexts())
    assert embedder.output_dim == 4
    vec = embedder.embed({"a": 0.1, "b": 0.2, "c": 0.3}, confidence=0.8)
    assert vec.shape == (4,)


def test_batch_matches_single_sample_embedding():
    embedder = FailureEmbedder(["a", "b", "c"], n_components=2).fit(_contexts())
    contexts = _contexts(n=5, seed=1)
    confidences = [0.1, 0.4, 0.5, 0.7, 0.99]
    batch = embedder.embed_batch(contexts, confidences)
    singles = np.stack([embedder.embed(c, conf) for c, conf in zip(contexts, confidences)])
    np.testing.assert_allclose(batch, singles)


def test_confidence_derived_features_are_correct():
    embedder = FailureEmbedder(["a", "b", "c"], n_components=1).fit(_contexts())
    vec = embedder.embed({"a": 0.0, "b": 0.0, "c": 0.0}, confidence=0.5)
    # confidence=0.5 -> both derived scalars (2*|c-0.5|, |c-0.5|) are 0
    assert vec[-2] == pytest.approx(0.0)
    assert vec[-1] == pytest.approx(0.0)
    vec2 = embedder.embed({"a": 0.0, "b": 0.0, "c": 0.0}, confidence=1.0)
    assert vec2[-2] == pytest.approx(1.0)
    assert vec2[-1] == pytest.approx(0.5)


def test_fit_handles_fewer_samples_than_requested_components():
    embedder = FailureEmbedder(["a", "b"], n_components=5)
    embedder.fit([{"a": 1.0, "b": 2.0}, {"a": 3.0, "b": 4.0}])
    vec = embedder.embed({"a": 1.0, "b": 1.0}, confidence=0.6)
    assert vec.shape[0] == embedder.output_dim
