import json
import re
import sys

from dataclasses import dataclass, replace
from typing import Optional

import numpy as np
import plotly.subplots
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from dacite import Config, from_dict

from eos import Eos
from ev_curve import EvCurve


pio.templates.default = "plotly_white"


@dataclass
class InputData:
    title: Optional[str]
    ev_curves: list[EvCurve]


def main():
    data = from_dict(
        data_class=InputData,
        data=json.load(sys.stdin),
        config=Config(type_hooks={Eos: Eos.from_id}, cast=[tuple])
    )

    ev_curves = data.ev_curves
    ref_data = np.genfromtxt(
        "asset/takimoto_a_si_beta.csv",
        skip_header=1,
        delimiter=","
    )

    ref_t, ref_beta = ref_data[:,0], ref_data[:,1]
    ref_t += 273.15
    ref_alpha = ref_beta * 3

    t = []
    v_0 = []
    b_0 = []

    for ev_curve in ev_curves:
        t_ = float(re.search(r"T = (\d+) K", ev_curve.label).group(1))

        if t_ == 700.0:
            continue

        v_0_ = ev_curve.eos_fit.params["V0"]
        b_0_ = ev_curve.eos_fit.params["B0"] * 160.21766208

        t.append(t_)
        v_0.append(v_0_)
        b_0.append(b_0_)

    t = np.array(t)
    v_0 = np.array(v_0)
    b_0 = np.array(b_0)

    alpha = [
        (((v_0[i+1] - v_0[i])) / (t[i+1] - t[i])) / (((v_0[i+1] + v_0[i])) / 2)
        for i in range(len(v_0) - 1)
    ]
    alpha = np.array(alpha)

    t2 = np.array([((t[i + 1] + t[i]) / 2) for i in range(len(t) - 1)])


    print("b0", file=sys.stderr)
    print(t, file=sys.stderr)
    print(b_0, file=sys.stderr)

    print("alpha", file=sys.stderr)
    print(t2, file=sys.stderr)
    print(alpha, file=sys.stderr)

    fig = plotly.subplots.make_subplots(
        rows=2,
        cols=1,
        vertical_spacing=0.1,
        shared_xaxes=True
    )

    fig.add_trace(
        go.Scatter(
            x=t,
            y=b_0,
            mode="markers",
            showlegend=False
        ),
        row=1,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=t2,
            y=alpha,
            mode="markers",
            name="DeepMD calculations"
        ),
        row=2,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=ref_t,
            y=ref_alpha,
            mode="markers",
            name="Takimoto et al. (2002)"
        ),
        row=2,
        col=1
    )

    fig.update_xaxes(
        showgrid=False,
        linewidth=1,
        linecolor="black",
        mirror="allticks",
        ticks="inside",
        showline=True,
        exponentformat="e"
    )

    fig.update_xaxes(
        title_text="$\large{T \, [\mathrm{K}]}$",
        col=1,
        row=2
    )

    fig.update_yaxes(
        title_text="$\large{B_0 \, [\mathrm{GPa}]}$",
        exponentformat="e",
        showgrid=False,
        linewidth=1,
        linecolor="black",
        mirror="allticks",
        ticks="inside",
        showline=True,
        row=1,
        col=1
    )

    fig.update_yaxes(
        title_text="$\large{\\alpha_\mathrm{V} \, [\mathrm{K}^{-1}]}$",
        exponentformat="e",
        showgrid=False,
        linewidth=1,
        linecolor="black",
        mirror="allticks",
        ticks="inside",
        showline=True,
        row=2,
        col=1,
        zeroline=False
    )

    fig.update_layout(
        font_size=19,
        font_color="#000",
        plot_bgcolor="#fff",
        legend=dict(
            x=.015,
            y=.27,
            traceorder="normal",
            bordercolor="#000",
            borderwidth=1
        ),
        margin=dict(l=1, r=1, b=1, t=1)
    )

    fig.write_image(sys.stdout.buffer, format="jpg")


if __name__ == "__main__":
    main()
