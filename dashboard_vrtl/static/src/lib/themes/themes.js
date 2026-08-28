/* amCharts 5 themes for dashboard_vrtl.
 *
 * The chart components reference the standard am5themes_* globals
 * (am5themes_Animated.new(root) etc.). The amcharts libs shipped with this
 * module do not expose the themes, so they are redefined here as classes
 * extending am5.Theme. Rule bodies sourced from the official amCharts 5
 * theme files (https://cdn.amcharts.com/lib/5/themes/).
 * NOTE: must be loaded AFTER the amcharts core (am5 global).
 */
(function () {
    if (typeof window === "undefined" || !window.am5 || !window.am5.Theme) {
        return;
    }
class Am5ThemeAnimated extends am5.Theme {
    setupDefaultRules() {
        super.setupDefaultRules(),this.rule("Component").setAll({interpolationDuration:600}),this.rule("Hierarchy").set("animationDuration",600),this.rule("Scrollbar").set("animationDuration",600),this.rule("Tooltip").set("animationDuration",300),this.rule("MapChart").set("animationDuration",1e3),this.rule("MapChart").set("wheelDuration",300),this.rule("Entity").setAll({stateAnimationDuration:600}),this.rule("Sprite").states.create("default",{stateAnimationDuration:600}),this.rule("Tooltip",["axis"]).setAll({animationDuration:200}),this.rule("WordCloud").set("animationDuration",500),this.rule("Polygon").set("animationDuration",600),this.rule("ArcDiagram").set("animationDuration",600);
    }
}
window.am5themes_Animated = Am5ThemeAnimated;
class Am5ThemeFrozen extends am5.Theme {
    setupDefaultRules() {
        super.setupDefaultRules(),this.rule("ColorSet").setAll({colors:[am5.Color.fromHex(12502264),am5.Color.fromHex(10857454),am5.Color.fromHex(6974942),am5.Color.fromHex(5063375),am5.Color.fromHex(7421581),am5.Color.fromHex(10576032),am5.Color.fromHex(15429296),am5.Color.fromHex(16095163),am5.Color.fromHex(16496841),am5.Color.fromHex(16307416)],reuse:!0});
    }
}
window.am5themes_Frozen = Am5ThemeFrozen;
class Am5ThemeKelly extends am5.Theme {
    setupDefaultRules() {
        super.setupDefaultRules(),this.rule("ColorSet").setAll({colors:[am5.Color.fromHex(15975168),am5.Color.fromHex(8869522),am5.Color.fromHex(15959040),am5.Color.fromHex(10603249),am5.Color.fromHex(12451890),am5.Color.fromHex(12759680),am5.Color.fromHex(8684674),am5.Color.fromHex(34902),am5.Color.fromHex(15110060),am5.Color.fromHex(26533),am5.Color.fromHex(16356217),am5.Color.fromHex(6311575),am5.Color.fromHex(16164352),am5.Color.fromHex(11748460),am5.Color.fromHex(14471936),am5.Color.fromHex(8924439),am5.Color.fromHex(9287168),am5.Color.fromHex(6636834),am5.Color.fromHex(14833698),am5.Color.fromHex(2833702),am5.Color.fromHex(15922164),am5.Color.fromHex(2236962)],reuse:!0});
    }
}
window.am5themes_Kelly = Am5ThemeKelly;
class Am5ThemeMaterial extends am5.Theme {
    setupDefaultRules() {
        super.setupDefaultRules(),this.rule("ColorSet").setAll({colors:[am5.Color.fromHex(16007990),am5.Color.fromHex(15277667),am5.Color.fromHex(10233776),am5.Color.fromHex(6765239),am5.Color.fromHex(4149685),am5.Color.fromHex(2201331),am5.Color.fromHex(240116),am5.Color.fromHex(48340),am5.Color.fromHex(38536),am5.Color.fromHex(5025616),am5.Color.fromHex(9159498),am5.Color.fromHex(13491257),am5.Color.fromHex(16771899),am5.Color.fromHex(16761095),am5.Color.fromHex(16750592),am5.Color.fromHex(16733986),am5.Color.fromHex(7951688),am5.Color.fromHex(10395294),am5.Color.fromHex(6323595)],reuse:!0});
    }
}
window.am5themes_Material = Am5ThemeMaterial;
class Am5ThemeMoonrise extends am5.Theme {
    setupDefaultRules() {
        super.setupDefaultRules(),this.rule("ColorSet").setAll({colors:[am5.Color.fromHex(3805954),am5.Color.fromHex(6296069),am5.Color.fromHex(9054989),am5.Color.fromHex(13065764),am5.Color.fromHex(13082457),am5.Color.fromHex(10786154),am5.Color.fromHex(8815977),am5.Color.fromHex(7696225),am5.Color.fromHex(5792096),am5.Color.fromHex(6388099)],reuse:!0});
    }
}
window.am5themes_Moonrise = Am5ThemeMoonrise;
class Am5ThemeSpirited extends am5.Theme {
    setupDefaultRules() {
        super.setupDefaultRules(),this.rule("ColorSet").setAll({colors:[am5.Color.fromHex(6648718),am5.Color.fromHex(7761041),am5.Color.fromHex(7886447),am5.Color.fromHex(5389144),am5.Color.fromHex(8469309),am5.Color.fromHex(12344914),am5.Color.fromHex(15633272),am5.Color.fromHex(16369797),am5.Color.fromHex(15442012),am5.Color.fromHex(10178868)],reuse:!0});
    }
}
window.am5themes_Spirited = Am5ThemeSpirited;
})();
