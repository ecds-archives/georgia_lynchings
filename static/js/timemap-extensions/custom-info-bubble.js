/** Custom Info Bubble for time map to allow for sliding map instead of traditional info bubble
*	Compatible with timemap.js
*	
*/

window.TimeMapExt = {};
window.TimeMapExt.RED_ICON = "http://www.google.com/intl/en_us/mapfiles/ms/icons/red-dot.png";
window.TimeMapExt.GREEN_ICON = "http://www.google.com/intl/en_us/mapfiles/ms/icons/green-dot.png";
window.TimeMapExt.current_marker = null;
window.TimeMapExt.restoreCurrent = function() {
	if (window.TimeMapExt.current_marker != null) {
		window.TimeMapExt.current_marker.getNativePlacemark().setIcon(window.TimeMapExt.RED_ICON);
	}
}
$(function() {
	if (window.TimeMap) {
		TimeMapItem.openInfoWindowBasic = function() {
		    // preserve this for use in callbacks
			var self = this;
			
			if (window.TimeMapExt.current_marker != self) {
				window.TimeMapExt.restoreCurrent();
				window.TimeMapExt.current_marker = self;
			}
			
			if (TimeMap.static_center == undefined) {
				TimeMap.static_center = self.map.getCenter();
			}
	
			var map_container = $("#mapcontainer");
			$("#details").css("height", map_container.height());
	
			var percent_width = 100*map_container.width()/map_container.parent().width();
			
			// change the marker, must go through native api (google v3) to do this
			self.getNativePlacemark().setIcon(window.TimeMapExt.GREEN_ICON);
			
			// make sure to animate only if visible
			if (percent_width == 100 && !$("#details").is(":visible")) {
				map_container.animate({"width" : map_container.width() * 0.7}, 250, complete = function() {
					$("#details").show();
				});
			}
			
			$("#detail-content").html(self.getInfoHtml());
			$("#details img.close").click(function() {
				// close info window and replace marker
				self.closeInfoWindow();
			});
			
			self.map.setCenter(self.placemark.location);
		};

		TimeMapItem.closeInfoWindowBasic = function() {
			//console.log(this);
			var map_container = $("#mapcontainer");
			var percent_width = 100*map_container.width()/map_container.parent().width();
	
			// :visible check fixes timemap scrolling
		   	if (percent_width < 100 && $("#details").is(":visible")) {
				$("#details").hide();
				$("#mapcontainer").animate({"width" : "100%"}, 500);
			}
			
			window.TimeMapExt.restoreCurrent();
		}; //end TimeMapItem.closeInfoWindowBasic
	}
});

