"""Convert's card before the batch (step 3): how many files will really be written, what happens
to the results that already exist (Settings' rule or Review's answer, feature 035, AC-08), and
where they go. A module of its own: the view stays within its size."""

from clearmd.frontend.presenter import Presenter
from clearmd.frontend.presenter.chrome.secondary import ready_line
from clearmd.frontend.ttk.views.choose import ChooseView
from clearmd.frontend.ttk.views.convert import ConvertView
from clearmd.frontend.ttk.views.review import ReviewView
from clearmd.frontend.ttk.window.shown import Shown


def show_ready(
    converting: ConvertView,
    shown: Shown,
    presenter: Presenter,
    review: ReviewView,
    main: ChooseView,
) -> None:
    setting = presenter.settings.on_existing_output
    line = ready_line(shown.catalog, shown.last_plan, setting, review.overwrite_answer())
    if line is not None:
        converting.show_ready(line, str(main.output_label.cget("text")))
