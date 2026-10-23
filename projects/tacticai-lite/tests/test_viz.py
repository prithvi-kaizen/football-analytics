import matplotlib.pyplot as plt
import numpy as np

from tacticai_lite.viz import pitch_figure


def test_vertical_pitch_preserves_normalized_player_coordinates():
    detail={'event':{'location':[120,80]},'frame':{'freeze_frame':[
        {'location':[110,60],'teammate':True},
        {'location':[113,50],'teammate':False}]}}
    fig=pitch_figure(detail,False)
    ax=fig.axes[0]
    np.testing.assert_allclose(ax.collections[0].get_offsets(),[[20,110]])
    np.testing.assert_allclose(ax.collections[1].get_offsets(),[[30,113]])
    np.testing.assert_allclose(ax.collections[2].get_offsets(),[[0,120]])
    plt.close(fig)


def test_pitch_missing_origin_has_visible_explanation():
    fig=pitch_figure({'event':{},'frame':None})
    assert any(t.get_text()=='Corner location unavailable' for t in fig.axes[0].texts)
    assert fig.axes[0].get_ylim()==(75,124)
    plt.close(fig)
