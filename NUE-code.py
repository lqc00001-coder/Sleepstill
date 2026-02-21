# -*- coding: utf-8 -*-

import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams['font.family'] = 'Times New Roman'
province_fontsize = 28
all_fontsize = 16
matplotlib.rcParams.update({
    'font.size': all_fontsize,         
    'axes.titlesize': all_fontsize,    
    'axes.labelsize': all_fontsize,    
    'xtick.labelsize': all_fontsize,   
    'ytick.labelsize': all_fontsize,   
    'legend.fontsize': all_fontsize,   
    'figure.titlesize': all_fontsize,  
})

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import warnings
#from matplotlib.offsetbox import AnchoredOffsetbox, TextArea, HPacker

try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


# Colors
COLOR_NUE = "#015AE5"
COLOR_BEN = "#E69800"
COLOR_YLD = "#39A702"


def avg_hex_from_image(path):
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow not available; cannot sample color from image.")
    im = Image.open(path).convert("RGBA")
    import numpy as np
    arr = np.asarray(im)
    if arr.shape[2] == 4:
        mask = arr[:, :, 3] > 0
        rgb = arr[:, :, :3][mask]
    else:
        rgb = arr.reshape(-1, 3)
    r, g, b = [int(round(v)) for v in rgb.mean(axis=0)]
    return "#{:02X}{:02X}{:02X}".format(r, g, b)



def load_local_practice_map(xlsx_path):
    """Load province -> NFert mapping from an Excel file.
    Tries to find sheet/columns flexibly: pname / fer_amount_mean or fer_amount.
    Returns a dict {province_name: value} with stripped province names.
    """
    try:
        xls = pd.ExcelFile(xlsx_path)
    except Exception as e:
        warnings.warn(f"Cannot open local NFert file '{xlsx_path}': {e}")

        return {}
    # try each sheet
    candidates = []
    for sh in xls.sheet_names:
        try:
            df = pd.read_excel(xlsx_path, sheet_name=sh)
            cols = {c.lower().strip(): c for c in df.columns}
            pname_col = cols.get("pname")
            val_col = cols.get("fer_amount_mean") or cols.get("fer_amount")
            if pname_col and val_col:
                tmp = df[[pname_col, val_col]].copy()
                tmp.columns = ["pname", "val"]
                candidates.append(tmp)
        except Exception:
            continue
    if not candidates:
        warnings.warn(f"No valid 'pname' + 'fer_amount_mean/fer_amount' found in '{xlsx_path}'.") 
        return {}
    data = pd.concat(candidates, ignore_index=True)
    data["pname"] = data["pname"].astype(str).str.strip()
    data["val"] = pd.to_numeric(data["val"], errors="coerce")
    data = data.dropna(subset=["pname","val"])
    # keep last occurrence per pname
    mp = {k: v for k, v in zip(data["pname"], data["val"])}
    return mp


def pick(df, like):
    key = like.lower().replace("_","").replace("-","").replace(" ","")
    for c in df.columns:
        if key in str(c).lower().replace("_","").replace("-","").replace(" ",""):
            return c
    return None


def set_black_frame(ax, sides=("top","right","left","bottom"), lw=1.2):
    for side in sides:
        if side in ax.spines:
            ax.spines[side].set_visible(True)
            ax.spines[side].set_color("#000000")
            ax.spines[side].set_linewidth(lw)


def main(args):
    # Load local practice NFert mapping (province -> value)
    local_map = load_local_practice_map(args.local_nfert_xlsx)

    xlsx_path = args.xlsx
    out_png = args.out_png
    out_pdf = args.out_pdf
    yield_offset = args.yield_offset
    frame_lw = args.frame_lw

    x_ticks = [int(s) for s in args.x_ticks.split(",")]

    # Max Benefit line color
    if args.maxline_swatch:
        maxline_color = avg_hex_from_image(args.maxline_swatch)
    else:
        maxline_color = args.maxline_hex

    xls = pd.ExcelFile(xlsx_path)
    sheet_names = xls.sheet_names

    rows, cols = 6, 5
    fig, axes = plt.subplots(rows, cols, figsize=(26, 28), constrained_layout=False)
    axes = axes.reshape(-1)

    for i, ax in enumerate(axes):
        if i >= len(sheet_names):
            ax.axis("off")
            continue

        name = sheet_names[i]
        df = pd.read_excel(xlsx_path, sheet_name=name)

        col_x   = pick(df, "N-Fert") or pick(df, "N_Fert") or pick(df, "Nfert") or pick(df, "N Fert")
        col_nue = pick(df, "NUE_sim") or pick(df, "NUE")
        col_b   = pick(df, "B_sim")  or pick(df, "Benefit")
        col_y   = pick(df, "Yield_sim") or pick(df, "Yield")

        if not all([col_x, col_nue, col_b, col_y]):
            ax.text(0.5, 0.5, "Missing columns", ha="center", va="center", transform=ax.transAxes)
            ax.set_axis_off()
            continue

        d = df[[col_x, col_nue, col_b, col_y]].dropna().sort_values(col_x)
        if d.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            ax.set_axis_off()
            continue

        x = d[col_x].to_numpy(float)
        nue = d[col_nue].to_numpy(float)
        ben = d[col_b].to_numpy(float)
        yld = d[col_y].to_numpy(float)

        if np.nanmax(nue) <= 1.5:
            nue *= 100.0

        # Primary axis frame (all four spines in black)
        ax.grid(False); ax.minorticks_off()
        set_black_frame(ax, sides=("top","right","left","bottom"), lw=frame_lw)

        # Explicit x tick marks (ensure visible)
        ax.tick_params(axis="x", which="major", length=5, width=1.0, direction="out")

        # NUE (left)
        ax.plot(x, nue, linewidth=1.6, color=COLOR_NUE)
        ax.set_yticks([0, 40, 80, 120])

        # Fixed sparse x ticks
        ax.set_xlim(0, 120)
        ax.set_xticks([0,40,80,120])#x_ticks
        ax.tick_params(axis='y', which='both',labelcolor=COLOR_NUE)

        # Benefit (right primary) — hide bottom/left spines to avoid covering x ticks
        ax_b = ax.twinx()
        ax_b.grid(False); ax_b.minorticks_off()
        set_black_frame(ax_b, sides=("top","right"), lw=frame_lw)
        # explicitly hide spines that could cover bottom ticks
        for s in ("bottom","left"):
            if s in ax_b.spines:
                ax_b.spines[s].set_visible(False)
        ax_b.plot(x, ben, linewidth=1.6, color=COLOR_BEN)
        ax_b.set_yticks([-200, 0, 200])
        ax_b.set_ylim(bottom=-500)
        ax_b.tick_params(labelcolor=COLOR_BEN)
        
        # Yield (right secondary) with uniform offset — also hide bottom/left spines
        ax_y = ax.twinx()
        ax_y.spines["right"].set_position(("axes", yield_offset))
        ax_y.set_frame_on(True)
        ax_y.patch.set_visible(False)
        ax_y.grid(False); ax_y.minorticks_off()
        set_black_frame(ax_y, sides=("top","right"), lw=frame_lw)
        for s in ("bottom","left"):
            if s in ax_y.spines:
                ax_y.spines[s].set_visible(False)
        ax_y.plot(x, yld, linewidth=1.6, color=COLOR_YLD)
        ax_y.set_yticks([2000, 4000])
        ax_y.set_ylim(bottom=2000)
        ax_y.tick_params(axis='y', which='both', labelcolor=COLOR_YLD)
        
        # Province label (bigger)
        ax.text(0.02, 0.08, name, transform=ax.transAxes, fontsize=province_fontsize, ha="left", va="bottom")
        # --- Local practice vertical line (dark grey) ---
        try:
            key = str(name).strip()
            if key in local_map:
                lp = float(local_map[key])
                # draw vertical line
                ax.axvline(x=lp, color="#555555", linewidth=1.6, linestyle="--")
                # annotate value at top of axis (use x-axis transform so y is in [0..1])
                # 2) 计算一个很小的横向偏移（按当前坐标范围的1%）
                xmin, xmax = ax.get_xlim()
                dx = 0.01 * (xmax - xmin)
                
                ax.text(lp+dx*3, 0.05, f"{lp:.0f}", color="#555555",
                        transform=ax.get_xaxis_transform(), ha="center", va="top")
        except Exception as _e:
            # keep silent to avoid changing layout/behavior if anything goes wrong
            pass


        # Max Benefit vertical line + label
        idx_max = int(np.nanargmax(ben))
        x_max = x[idx_max]
        ax.axvline(x=x_max, color=maxline_color, linewidth=1.8)
        ax.text(x_max + 0.8, 0.05, f"{int(round(x_max))}", color=maxline_color,
                transform=ax.get_xaxis_transform(), ha="left", va="top")

    # set xylabel text
    for ax in axes:
        ax.set_ylabel("NUE (kg/kg)") 
        ax.set_xlabel("N-fert (kg/ha)")
# =============================================================================
#         ta_y = TextArea("Yield",    textprops=dict(color=COLOR_YLD))
#         ta_bar = TextArea(" | ",    textprops=dict(color="black"))
#         ta_b = TextArea("Benefit",  textprops=dict(color=COLOR_BEN))
# 
#         hpack = HPacker(children=[ta_y, ta_bar, ta_b],
#                     align="center", pad=0, sep=2)  # sep 调整三者间距
# 
#         anchored = AnchoredOffsetbox(
#             loc="upper right", child=hpack, frameon=False,
#             bbox_to_anchor=(0.99, 0.99), bbox_transform=ax.transAxes, borderpad=0.0, pad=0.0
#             )
#         ax.add_artist(anchored)
# =============================================================================
    #for r in range(rows):
        #axes[r*cols + 0].set_ylabel("NUE (kg/kg)")
        #axes[r*cols + (cols-1)].set_ylabel("")

    # Spacing & margins (defaults: wider horizontal spacing)
    plt.subplots_adjust(left=args.left, right=args.right, top=args.top, bottom=args.bottom,
                        wspace=args.wspace, hspace=args.hspace)

# =============================================================================
#     # Legend
#     handles = [
#         Line2D([0],[0], color=COLOR_NUE, linewidth=2, label="NUE (kg/kg)"),
#         Line2D([0],[0], color=COLOR_BEN, linewidth=2, label="Benefit (USD$/ha)"),
#         Line2D([0],[0], color=COLOR_YLD, linewidth=2, label="Yield (kg/ha)"),
#         Line2D([0],[0], color=maxline_color, linewidth=2, label="Max Benefit-Nfert (kg/ha)"),
#         Line2D([0],[0], color="#555555", linewidth=2, linestyle="--", label="Local practice_Nfert (kg/ha)"),
#     ]
#     fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 0.965))
# =============================================================================

    fig.savefig(out_png, dpi=1000)
    fig.savefig(out_pdf)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--xlsx", default="data.xlsx")
    p.add_argument("--out_png", default="NUE_1015.png")
    p.add_argument("--out_pdf", default="NUE_1015.pdf")
    p.add_argument("--yield_offset", type=float, default=1.0)
    p.add_argument("--maxline_hex", default="#E60000")
    p.add_argument("--maxline_swatch", default=None)
    p.add_argument("--frame_lw", type=float, default=1.2)
    p.add_argument("--x_ticks", default="20,60,100")
    p.add_argument("--province_fontsize", type=float, default=12)
    p.add_argument("--local_nfert_xlsx", default="province_fer_amount_mean.xlsx")
    # margins & spacing
    p.add_argument("--left", type=float, default=0.06)
    p.add_argument("--right", type=float, default=0.93)
    p.add_argument("--top", type=float, default=0.90)
    p.add_argument("--bottom", type=float, default=0.08)
    p.add_argument("--wspace", type=float, default=0.40)
    p.add_argument("--hspace", type=float, default=0.30)
    args = p.parse_args()
    main(args)
