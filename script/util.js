var map = undefined;
var fpoi = 'https://cdn.rawgit.com/cdawei/path_vis/master/data/poi-Melb-all.csv';
var colors = ["#345E9D","#7A2947","#47C29D","#78349D","#8BCF6E","#E1E2A7","#C4684F","#4787C2","#BFA640","#C79FDF"]

function draw_map() {
    var latMelb = -37.815018
    var lngMelb = 144.97
    map = new GMaps({
        div: '#map',
        lat: latMelb,
        lng: lngMelb,
        zoom: 15
    });
    // properties of the Map object
    //for (var prop in map) {
    //    console.log('map property: ' + prop);
    //}
}


function draw_POIs() {
    if (map === undefined) {
        draw_map();
    }
    d3.csv(fpoi, function(data) {
        var pois = {};
        data.forEach(function(d) {
            pois[d.poiID] = {
                "name": d.poiName,
                "category": d.poiTheme,
                "lat": d.poiLat,
                "lng": d.poiLon,
                "url": d.poiURL,
                "popularity": d.poiPopularity
           };
        });
        for (var pid in pois) {
            var pi = pois[pid]
            map.addMarker({
                lat: pi["lat"],
                lng: pi["lng"],
                //title: pi["category"],
                poiID: pid,  //custom property
                infoWindow: {content: '<p>POI: &nbsp;' + pi["name"] + ',&nbsp;' + pi["category"] + ',&nbsp;' + pid + '</p>'},
                click: function(e) {
                    // set the start point
                    document.getElementById("ID_marker").innerHTML = "<font color=\"red\">" + this.poiID + "</font>";
                    document.getElementById("ID_start").value = this.poiID;
                    console.log('set the start point to ' + this.poiID);
                },
                mouseover: function() {
                    this.infoWindow.open(this.map, this);
                },
                mouseout: function() {
                    this.infoWindow.close();
                }
            });
        }
    });
}


function draw_route(traj, color, travel_mode="walking") {
    //travel_mode: driving, bicycling or walking
    if (map === undefined) {
        draw_map();
    }
    d3.csv(fpoi, function(data) {
        var pois = {};
        data.forEach(function(d) {
            pois[d.poiID] = {
                "name": d.poiName,
                "category": d.poiTheme,
                "lat": d.poiLat,
                "lng": d.poiLon,
                "url": d.poiURL,
                "popularity": d.poiPopularity
           };
        });
        var waypts = []; //way points
        for (var i = 1; i < traj.length-1; i++) {
            pi = pois[ traj[i] ];
            waypts.push({
                location: new google.maps.LatLng(pi["lat"], pi["lng"]),
                stopover: true
            });
        }
        ps = pois[ traj[0] ];
        pt = pois[ traj[traj.length-1] ];
        map.drawRoute({
            origin: [ ps["lat"], ps["lng"] ],
            destination: [ pt["lat"], pt["lng"] ],
            waypoints: waypts,
            optimizeWaypoints: false, //do NOT allow way points to be reordered
            travelMode: travel_mode,
            strokeColor: color, //RRGGBB, e.g. '#1F5566', '#131540'
            strokeOpacity: 0.6,
            strokeWeight: 6,
            fillColor: "#0000FF",
            fillOpacity: 0.4
        });
    });
    console.log('trajectory: ' + traj);
    //console.log(travel);
}


function parse_draw(response) {
    var trajdata = JSON.parse(response);
    console.log(trajdata);
    var trajs = [trajdata[0]['Trajectory'], trajdata[1]['Trajectory']];
    //trajs = response.split(";");
    //console.log(trajs);
    //console.log(trajs.length);
    for (var i = 0; i < trajs.length; i++) {
        /*
        var trajstr = trajs[i].split(",");
        var traj = [];
        for (var j = 0; j < trajstr.length; j++) {
            traj.push(parseInt(trajstr[j]));
        }
        */
        traj = trajs[i];
        //console.log(traj);
        color = colors[i]
        travel = document.getElementById("ID_select").value;
        draw_route(traj, color, travel);

    }
}
