TimeMapItem.openInfoWindowBasic = function() {
    console.log(this);
	var self = this;
    
	var map = $("#mapcontainer");
	$("#details").css("height", map.height());
	var percentWidth = 100*map.width()/map.parent().width();
	
	// make sure to animate only if visible
	if (percentWidth == 100 && !$("#details").is(":visible")) {
		map.animate({"width" : map.width() * 0.7}, 250, complete = function() {
			
			$("#details").show();
		});
	}
	$("#detail-content").html(self.getInfoHtml());
			
	console.log("openwindow");
};

TimeMapItem.closeInfoWindowBasic = function() {
	var map = $("#mapcontainer");
	console.log($("#details").is(":visible"));
	var percentWidth = 100*map.width()/map.parent().width();
	
	// :visible check fixes timemap scrolling
   	if (percentWidth < 100 && $("#details").is(":visible")) {
		$("#details").hide();
		$("#mapcontainer").animate({"width" : "100%"}, 500);
	}
};