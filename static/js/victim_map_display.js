/*
Most of this code is taken from with small modifications from the
documentation on the Google developer tutorials at
 https://developers.google.com/maps/documentation/javascript/
 */

var map;
var markersArray = [];

function initializeMap() {
    var myOptions = {
        center: new google.maps.LatLng(32.300, -82.400),
        panControl: false,
        zoomControl: true,
        mapTypeControl: false,
        scaleControl: true,
        streetViewControl: false,
        overviewMapControl: false,
        zoom: 5,
        mapTypeId: google.maps.MapTypeId.TERRAIN
    };
    map = new google.maps.Map(document.getElementById("map_canvas"),
        myOptions);
}

function addMarker(location, markerTitle) {
    marker = new google.maps.Marker({
        position: location,
        map: map,
        title: markerTitle
    });
    markersArray.push(marker);
}

// Removes the overlays from the map, but keeps them in the array
function clearOverlays() {
    if (markersArray) {
        for (i in markersArray) {
            markersArray[i].setMap(null);
        }
    }
}

// Shows any overlays currently in the array
function showOverlays() {
    if (markersArray) {
        for (i in markersArray) {
            markersArray[i].setMap(map);
        }
    }
}

// Deletes all markers in the array by removing references to them
function deleteOverlays() {
    if (markersArray) {
        for (i in markersArray) {
            markersArray[i].setMap(null);
        }
        markersArray.length = 0;
    }
}