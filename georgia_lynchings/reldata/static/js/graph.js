/* Originally based on sample code from:
 *   http://mbostock.github.com/d3/ex/force.html
 * which is copyright 2012 Mike Bostock
 */


/***
 * NODE POSITIONING
 */

var colors20 = d3.scale.category20();

/* transfer node location from outgoing set to the new set
 * according to name so that the nodes stay in the same place. */
function init_node_locations(dest, src) {
  var center_y = $("#graph").attr("height") / 2;
  var delta_radius = center_y / dest.length;

  /* collect the outgoing nodes by name */
  var node_map = {};
  if (typeof src !== "undefined") {
    for (var i in src) {
      var node = src[i];
      node_map[node.name] = node;
    }
  }

  /* transfer locations to the incoming nodes */
  for (var i in dest) {
    var node = dest[i];
    if (node.name in node_map) {
      old_node = node_map[node.name];
      node.x = old_node.x;
      node.y = old_node.y;
      node.px = old_node.px;
      node.py = old_node.py;
    } else {
      position_new_node(i, node, delta_radius);
    }
  }
}

function position_new_node(i, node, delta_radius) {
  /* Rather than placing all nodes at 0,0, spiral them out from the
   * center using the golden ratio. Mostly our goal here is to
   * reduce initial erratic movement caused by placing them all on top
   * each other at 0,0. There's nothing special about this particular
   * algorithm besides the fact that it's been in use by plants for a
   * few eons. */
  var center_x = $("#graph").attr("width") / 2;
  var center_y = $("#graph").attr("height") / 2;

  var angle = 0.618 * i; // phi-1
  var radius = i * delta_radius;
  node.x = node.px = center_x + radius * Math.cos(angle);
  node.y = node.py = center_y + radius * Math.sin(angle);
}

/***
 * HANDLE DATA CHANGE
 */

function load_graph_data(url, force) {
  d3.json(url, function(json) {
    init_node_locations(json.nodes, force.nodes());
    force.nodes(json.nodes)
         .links(json.links);
    update_nodes_on_data_change(json, force);
    update_links_on_data_change(json, force);
    force.start();
  });
}

function get_filtered_graph_data(url, force) {
  var query = "?";
  $("select.filter").each(function() {
    if ($(this).val()) {
      query += $(this).attr("name") + "=" + $(this).val() + "&";
    }
  });
  query = query.substring(0, query.length - 1);
  load_graph_data(url + query, force);
}

function update_nodes_on_data_change(json, force) {
  var nodes_group = d3.select("#nodes");

  /* create the nodes. a node is a g containing a circle and text.
   * this allows us to keep the circle marker and the label together
   * in a single element */
  var nodes = nodes_group.selectAll("g.node")
      .data(json.nodes, function (d) { return d.name; });
  /* enter nodes */
  var enter_nodes = nodes.enter().append("g")
      .classed("node", true)
      .style("opacity", 0) /* transition to 1 below */
      .call(force.drag)
      .on('click.select', select_node);
  enter_nodes
    .transition()
      .duration(500)
      .style("opacity", 1);
  enter_nodes.append("circle")
      .style("fill", function (d) { return colors20(Math.ceil(d.weight / 5)); })
  enter_nodes.append("text")
      .classed("label", true)
      .attr("dy", ".3em")
      .attr("text-anchor", "middle")
      .text(function(d) { return d.name; });
  /* exit nodes */
  nodes.exit()
    .transition()
      .style("opacity", 0)
      .remove();
  /* attrs for update and enter notes */
  nodes.select("circle")
    .transition()
      .attr("r", function (d) {
        return d.weight * 0.6 + 6;
      });
}

function update_links_on_data_change(json, force) {
  var links_group = d3.select("#links");

  /* TODO: look into svg line markers to add direction arrows */
  var lines = links_group.selectAll("line.link")
      .data(json.links, function (d) {
          return d.source_name + "|" + d.target_name;
      });
  lines
    .transition()
      .style("stroke-width", function (d) {
        return d.value * 0.8 + 1;
      });
  lines.enter().append("line")
      .classed("link", true)
      .style("opacity", 0)
      .style("stroke-width", function (d) {
        return Math.sqrt(d.value) * 1.25;
      })
    .transition()
      .duration(2000)
      .style("opacity", 1);
  lines.exit().transition()
      .style("opacity", 0)
      .remove();
}

/***
 * HANDLE TICK
 */

function update_dom_on_tick() {
  var links_group = d3.select("#links");
  var nodes_group = d3.select("#nodes");

  links_group.selectAll("line.link")
    .attr("x1", function (d) { return d.source.x; })
    .attr("y1", function (d) { return d.source.y; })
    .attr("x2", function (d) { return d.target.x; })
    .attr("y2", function (d) { return d.target.y; });

  nodes_group.selectAll("g.node")
    .attr("transform", function (d) {
        return "translate(" + d.x + "," + d.y + ")";
    });
}

/***
 * NODE SELECTION
 */
function select_node(d) {
  console.log(d);
  d3.selectAll("#nodes .node")
    .classed("selected", false);
  d3.select(this).classed("selected", true);

  d3.selectAll("#links .link")
    .classed("selected", function(link) {
      return link.source == d || link.target == d;
    });

  // FIXME: hardcoded url here. should find some way to pass it in.
  var events_url = '/relations/graph/events/?participant=' + d.name;
  $.get(events_url, function(events) {
    update_sidebar_events(d, events)
  });
}

function update_sidebar_events(node_data, events) {
  var html = "<p><em>" + node_data.name + "</em> appears as an actor " +
             "description " + node_data.weight + " times in the following " +
             events.length + " stories:</p>";
  html += "<ul>";
  for (i in events) {
    var ev_html = '<li><a href="' + events[i].url + '">' +
                  events[i].name + '</a> ' +
                  '<span class="matches">(' + events[i].appearances + ')</span></li>';
    html += ev_html;
  }
  html += "</ul>";

  $("#graph_infobar_content").html(html);
}
