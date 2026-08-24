/* amCharts 5 theme aliases.
 *
 * The amcharts bundle (bundle.js) exposes the themes under the module names
 * am5_Animated, am5_Kelly, ... while the chart components reference the
 * standard am5themes_* names. This file must be loaded AFTER bundle.js.
 */
if (typeof window !== "undefined") {
    window.am5themes_Animated = window.am5_Animated;
    window.am5themes_Dark = window.am5_Dark;
    window.am5themes_Frozen = window.am5_Frozen;
    window.am5themes_Kelly = window.am5_Kelly;
    window.am5themes_Material = window.am5_Material;
    window.am5themes_Micro = window.am5_Micro;
    window.am5themes_Moonrise = window.am5_Moonrise;
    window.am5themes_Responsive = window.am5_Responsive;
    window.am5themes_Spirited = window.am5_Spirited;
}
