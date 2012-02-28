var build_jafar_client = function(cb) {
    var url = '';

    var serialize = function(obj) {
	var str = [];
	for(var p in obj)
	    str.push(encodeURIComponent(p) + "=" + encodeURIComponent(obj[p]));
	return str.join("&");
    }

    var call_url = function(details) {
	return function(settings, cb) {
	    if (Object.keys(settings).length == 0) {
		$.ajax({
		    url:details['path'],
		    type:"GET",
		    success: function(data) {
			if (cb) {
			    cb(data);
			}
		    }
		});
	    } else {
		$.ajax({
		    url:details['path'],
		    type:"GET",
		    data:serialize(settings),
		    success: function(data) {
			if (cb) {
			    cb(data);
			}
		    }
		});
	    }
	};
    }

    var the_client = function() {};
    $.get(url + '/_api_list/', function(data) {
	var d = JSON.parse(data);
	for(var index in d) {
	    var method = d[index][0];
	    var path = d[index][1];
	    var details = d[index][2];

	    var chunks = details['path'].slice(1);

	    genie.dig_set(the_client, chunks, call_url(details));
	}

	cb(the_client);
	console.log("post cb");
    });
};

