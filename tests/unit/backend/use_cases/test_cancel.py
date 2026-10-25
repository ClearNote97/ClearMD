import threading

from clearmd.backend.use_cases.cancel import CancelToken


def test_new_token_is_not_cancelled() -> None:
    assert not CancelToken().is_set()


def test_cancel_is_visible_from_another_thread() -> None:
    token = CancelToken()
    threading.Thread(target=token.cancel).start()
    assert token.wait(timeout=2)
    assert token.is_set()


def test_wait_times_out_when_nobody_cancels() -> None:
    assert not CancelToken().wait(timeout=0.01)
