/** Custom Info Bubble for time map to allow for sliding map instead of traditional info bubble
*   Compatible with timemap.js
*   
*/

// static class vars and methods
window.TimeMapExt = {};
window.TimeMapExt.RED_ICON = "http://www.google.com/intl/en_us/mapfiles/ms/icons/red-dot.png";
window.TimeMapExt.GREEN_ICON = "http://www.google.com/intl/en_us/mapfiles/ms/icons/green-dot.png";
window.TimeMapExt.current_marker = null;
window.TimeMapExt.restoreCurrent = function() {
    if (window.TimeMapExt.current_marker != null) {
        window.TimeMapExt.current_marker.getNativePlacemark().setIcon(window.TimeMapExt.RED_ICON);
    }
}

// wait for doc ready and only if TimeMap is defined
$(function() {
    if (window.TimeMap) {
        TimeMapItem.openInfoWindowBasic = function() {
            // preserve this for use in callbacks
            var self = this;
            
            // for use in icon swapping
            if (window.TimeMapExt.current_marker != self) {
                window.TimeMapExt.restoreCurrent();
                window.TimeMapExt.current_marker = self;
            }
            
            if (TimeMapExt.static_center == undefined) {
                TimeMapExt.static_center = self.map.getCenter();
                TimeMapExt.map = self.map;
            }
    
            var map_container = $("#mapcontainer");

            $("#details").css("height", map_container.height());
            
            // hack to get width in terms of width
            var percent_width = 100*map_container.width()/map_container.parent().width();
            
            // change the marker, must go through native api (google v3) to do this
            self.getNativePlacemark().setIcon(window.TimeMapExt.GREEN_ICON);
            
            // make sure to animate only if visible
            if (percent_width == 100 && !$("#details").is(":visible")) {
                map_container.animate({"width" : Math.round(map_container.width() * 0.75)}, 250, complete = function() {
                    $("#details").width(map_container.parent().width() - map_container.width());
                    $("#details").show();
                });
            }
            
            // populate details with rendered infoTemplate 
            $("#detail-content").html(self.getInfoHtml());
            
            // listener for the close icon
            $("#details img.close").click(function() {
                // close info window and replace marker
                self.closeInfoWindow();
            });
            
            // set center on selected icon
            // TODO: consider also calling a resize on the map itself to get new dimensions
            self.map.setCenter(self.placemark.location);
        };

        TimeMapItem.closeInfoWindowBasic = function() {
            // consider moving this to static function
            var map_container = $("#mapcontainer");
            var percent_width = 100*map_container.width()/map_container.parent().width();
    
            // :visible check fixes timemap scrolling
            if (percent_width < 100 && $("#details").is(":visible")) {
                $("#details").hide();
                $("#mapcontainer").animate({"width" : "100%"}, 500, complete = function() {
                    if (TimeMapExt.static_center) {
                        TimeMapExt.map.setCenter(TimeMapExt.static_center);
                    }
                });
            }
            
            // always restore red icon
            window.TimeMapExt.restoreCurrent();
        }; //end TimeMapItem.closeInfoWindowBasic
    }
});

