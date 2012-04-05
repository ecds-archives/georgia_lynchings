function init_timemap(url){
var tm;
// execute after the DOM is ready
$(document).ready(function() {

       tm = TimeMap.init({
           mapId: "map",               // Id of map div element (required)
           timelineId: "timeline",     // Id of timeline div element (required)
           options: {
               eventIconPath: "timemap/images/"
           },
           datasets: [{
             options: {
                 id:"event",
                 title:"Events",
                 theme:"red",
                 // Data to be loaded in JSON from a URL
                 type: "json_string",
                 url: url,
                 infoTemplate: "<div><b>{{title}}</b></div><div>Start Date: {{min_date}}</div><div>Location: {{county}} County</div><div>Alleged Crime: {{victim_allegedcrime_brundage_filter}}</div><div><a target='_blank' href='{{detail_link}}'>more info</a></div>"
             }

           }],
           bandIntervals: [
               Timeline.DateTime.MONTH,
               Timeline.DateTime.DECADE
           ],
                // may want to adjust this date to get different initial results
           scrollTo: TimeMap.dateParsers.hybrid("Jul 15 1890")
           });

           // filter function for tags
           var hasSelectedTag = function(item) {
           // if no tag was selected, everything passes
           return !window.selectedTag || (
                   // item has tags?
                   item.opts.tags &&
                   // tag found? (note - will work in IE; Timemap extends the Array prototype if necessary)
                   item.opts.tags.indexOf(window.selectedTag) >= 0
               );
       };

       // add our new function to the map and timeline filters
       tm.addFilter("map", hasSelectedTag); // hide map markers on fail
       tm.addFilter("timeline", hasSelectedTag); // hide timeline events on fail

       // onChange handler for pulldown menu
       $('#ac_tag_select').change(function() {
            window.selectedTag = $(this).val();
            // run filters
            tm.filter('map');
            tm.filter('timeline');
       });
       
});
}
