TimeMapItem.openInfoWindowBasic = function() {
    console.log(this);
    boxText = "<div class='info-window'>" + this.getInfoHtml() + "</div>";
    var options = {
        content: boxText,
        disableAutoPan: false,
        pixelOffset: new google.maps.Size(-140, -(32 + 130)),
        boxStyle: {
            backgroundColor: '#fff',
            opacity: 0.85,
            width: "280px",
            height: "120px",
            borderRadius: "6px"
        },
        infoBoxClearance: new google.maps.Size(1, 1)
    };
    if (TimeMap.ib) this.closeInfoWindow();
    TimeMap.ib = new InfoBox(options);
    TimeMap.ib.open(this.map.getMap(), this.getNativePlacemark());
};

TimeMapItem.closeInfoWindowBasic = function() {
    if (TimeMap.ib) TimeMap.ib.close();
};