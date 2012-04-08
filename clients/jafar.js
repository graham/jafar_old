var build_jafar_client = function(cb_build) {
    var url = '';

    var serialize = function(obj) {
	var str = [];
	for(var p in obj)
	    str.push(encodeURIComponent(p) + "=" + encodeURIComponent(obj[p]));
	return str.join("&");
    }

    var call_url = function(details) {
	return function(settings, cb) {
            if (settings == undefined) {
                settings = {};
            }
            if (settings.constructor == Function) {
                cb = settings;
                settings = {};
            }

            for(var key in settings) {
                var obj = settings[key];
                if (obj.constructor == Array ||
                    obj.constructor == Object) {
                    settings[key] = JSON.stringify(settings[key]);
                }
            }

            var d = {
                url:'/' + details['fullpath'],
                type:details['method'],
                success: function(data) {
                    if (cb) {
                        cb(JSON.parse(data));
                    }
                }
            }
            
	    if (Object.keys(settings).length != 0) {
                d['data'] = serialize(settings);
	    }

            if (cb == undefined) {
                d['async'] = false;
                var response = $.ajax(d);
                return JSON.parse(response.responseText);
            } else {
                return $.ajax(d);
            }
	};
    }

    var build_proxy = function(data) {
        var the_client = function() {};
        var a_proxy = function() {};
	var d = JSON.parse(data);
        var path_list = [];

        var dd = [];
        var thekeys = d[0];
        var thedata = d.slice(1);
        for(var index in thedata) {
            var kv = {};
            for(var ki in thekeys) {
                kv[thekeys[ki]] = thedata[index][ki];
            }
            dd.push(kv);
        }

        d = dd;

	for(var index in d) {
	    var details = d[index];
            console.log(details);
               
            path_list.push(d[index]['fullpath']);

	    var chunks = details['path'].slice(1);
	    var results = genie.dig_set(the_client, chunks, call_url(details), {'def':function() { return new a_proxy(); }});

            if (results[0]['__api_calls'] == undefined) {
                results[0]['__api_calls'] = [];
            }
            results[0]['__api_calls'].push(results[1]);
	}

        the_client.toString = function() {
            return "[JafarClient - " + path_list.length + " api calls]";
        };
        the_client.__path_list = path_list;
	return the_client;
    };

    if (cb_build == undefined) {
        var r = $.ajax( {
                url:'/_api_list/',
                method:"GET",
                async: false
            });
        return build_proxy(r.responseText);
    } else {
        $.get(url + '/_api_list/', function(data) {
                var ccc = build_proxy(data);
                return cb_build(ccc);
            });
    }
};

