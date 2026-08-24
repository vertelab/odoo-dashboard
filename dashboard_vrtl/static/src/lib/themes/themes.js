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
        super.setupDefaultRules(),this.rule("ColorSet").setAll({colors:[u.Q1.fromHex(12502264),u.Q1.fromHex(10857454),u.Q1.fromHex(6974942),u.Q1.fromHex(5063375),u.Q1.fromHex(7421581),u.Q1.fromHex(10576032),u.Q1.fromHex(15429296),u.Q1.fromHex(16095163),u.Q1.fromHex(16496841),u.Q1.fromHex(16307416)],reuse:!0});
    }
}
window.am5themes_Frozen = Am5ThemeFrozen;
class Am5ThemeKelly extends am5.Theme {
    setupDefaultRules() {
        super.setupDefaultRules(),this.rule("ColorSet").setAll({colors:[f.Q1.fromHex(15975168),f.Q1.fromHex(8869522),f.Q1.fromHex(15959040),f.Q1.fromHex(10603249),f.Q1.fromHex(12451890),f.Q1.fromHex(12759680),f.Q1.fromHex(8684674),f.Q1.fromHex(34902),f.Q1.fromHex(15110060),f.Q1.fromHex(26533),f.Q1.fromHex(16356217),f.Q1.fromHex(6311575),f.Q1.fromHex(16164352),f.Q1.fromHex(11748460),f.Q1.fromHex(14471936),f.Q1.fromHex(8924439),f.Q1.fromHex(9287168),f.Q1.fromHex(6636834),f.Q1.fromHex(14833698),f.Q1.fromHex(2833702),f.Q1.fromHex(15922164),f.Q1.fromHex(2236962)],reuse:!0});
    }
}
window.am5themes_Kelly = Am5ThemeKelly;
class Am5ThemeMaterial extends am5.Theme {
    setupDefaultRules() {
        super.setupDefaultRules(),this.rule("ColorSet").setAll({colors:[f.Q1.fromHex(16007990),f.Q1.fromHex(15277667),f.Q1.fromHex(10233776),f.Q1.fromHex(6765239),f.Q1.fromHex(4149685),f.Q1.fromHex(2201331),f.Q1.fromHex(240116),f.Q1.fromHex(48340),f.Q1.fromHex(38536),f.Q1.fromHex(5025616),f.Q1.fromHex(9159498),f.Q1.fromHex(13491257),f.Q1.fromHex(16771899),f.Q1.fromHex(16761095),f.Q1.fromHex(16750592),f.Q1.fromHex(16733986),f.Q1.fromHex(7951688),f.Q1.fromHex(10395294),f.Q1.fromHex(6323595)],reuse:!0});
    }
}
window.am5themes_Material = Am5ThemeMaterial;
class Am5ThemeMoonrise extends am5.Theme {
    setupDefaultRules() {
        super.setupDefaultRules(),this.rule("ColorSet").setAll({colors:[s.Q1.fromHex(3805954),s.Q1.fromHex(6296069),s.Q1.fromHex(9054989),s.Q1.fromHex(13065764),s.Q1.fromHex(13082457),s.Q1.fromHex(10786154),s.Q1.fromHex(8815977),s.Q1.fromHex(7696225),s.Q1.fromHex(5792096),s.Q1.fromHex(6388099)],reuse:!0});
    }
}
window.am5themes_Moonrise = Am5ThemeMoonrise;
class Am5ThemeSpirited extends am5.Theme {
    setupDefaultRules() {
        super.setupDefaultRules(),this.rule("ColorSet").setAll({colors:[u.Q1.fromHex(6648718),u.Q1.fromHex(7761041),u.Q1.fromHex(7886447),u.Q1.fromHex(5389144),u.Q1.fromHex(8469309),u.Q1.fromHex(12344914),u.Q1.fromHex(15633272),u.Q1.fromHex(16369797),u.Q1.fromHex(15442012),u.Q1.fromHex(10178868)],reuse:!0});
    }
}
window.am5themes_Spirited = Am5ThemeSpirited;
})();
