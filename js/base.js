function UI() {}
UI.prototype.pagination = function(ct, page, action) {
	var _html = "<ul>";
	if (page.number == 1) {
		_html += "<li class='active'><span>1</span></li>";
	} else {
		_html += "<li><a href='javascript: eval(\"" + action + "(1)\");'>1</a>";
	}
	
	var _begin = 2;
	var _end = page.totalPages - 1;
	if (page.totalPages > 11) {
		if (page.number <= 6) {
			_end = 10;
		} else if (page.number > (page.totalPages - 6)) {
			_begin = _end - 8;
		} else {
			_begin = page.number - 4;
			_end = page.number + 4;
		}
	}
	
	if (page.number > 6 && page.totalPages > 11) {
		_html += "<li><a title='第" + (_begin - 1) + "页' href='javascript: eval(\"" + action + "(" + (_begin - 1) + ")\");'>&laquo;</a></li>";
	}
	for (var i = _begin; i <= _end; i++) {
		if (i == page.number) {
			_html += "<li class='active'><span>" + i + "</span></li>";
		} else {
			_html += "<li><a href='javascript: eval(\"" + action + "(" + i + ")\");'>" + i + "</a></li>";
		}
	}
	if (page.totalPages > 11 && (page.totalPages - page.number > 5)) {
		_html += "<li><a title='第" + (_end + 1) + "页' href='javascript: eval(\"" + action + "(" + (_end + 1) + ")\");'>&raquo;</a></li>";
	}
	
	if (page.totalPages > 1) {
		if (page.number == page.totalPages) {
			_html += "<li class='active'><span>" + page.totalPages + "</span></li>";
		} else {
			_html += "<li><a href='javascript: eval(\"" + action + "(" + page.totalPages + ")\");'>" + page.totalPages + "</a></li>";
		}
	}
	_html += "</ul>";
	$(ct).addClass("pagination").addClass("pagination-right").html($(_html));
}

UI.prototype.alert = function(msg, title, type) {
	var alertBox = $("#alert-box");
	if (alertBox.length <= 0) { return; }
	alertBox.empty();
	var _msg = $("<div class='alert " + type + "'>\
		<button type='button' class='close' data-dismiss='alert'>×</button>\
		<strong>" + title + "</strong> " + msg + "</div>").appendTo(alertBox);
	if (type == "alert-success") {
		_msg.slideToggle(2000, function() { _msg.remove(); });
	}
}
UI.prototype.notice = function(msg) { this.alert(msg, "通知", "alert-success"); }
UI.prototype.info = function(msg) { this.alert(msg, "消息", "alert-info"); }
UI.prototype.warn = function(msg) { this.alert(msg, "警告!", ""); }
UI.prototype.error = function(msg) { this.alert(msg, "错误!", "alert-error"); }

UI.prototype.confirm = function(msg, commit, cancel) {
	var _dialog = $("<div class='modal hide' style='width: 320px; margin-left: -160px;'>\
						<div class='modal-header'><button type='button' class='close close-dialog'>×</button><h3 class='font-yahei'>确认?</h3></div>\
						<div class='modal-body'><p style='word-wrap: break-word;'>" + msg + "</p></div>\
						<div class='modal-footer'><button class='btn btn-primary'>确定</button><button class='btn close-dialog'>取消</button></div>\
					</div>").appendTo("body");
	_dialog.modal({backdrop: "static"});
	_dialog.find(".btn-primary").click(function() {
		_dialog.modal("hide");
		if (commit) { commit(); }
	});
	_dialog.find(".close-dialog").click(function() {
		_dialog.modal("hide");
		if (cancel) { cancel(); }
	});
	_dialog.on("hidden", function () { _dialog.remove(); })
}

UI.prototype.request = function(url, type, data, options) {
	if (!options) {
		options = {};
		if (!data) {
			data = {};
		} else if ($.isFunction(data)) {
			options.success = data;
			data = {};
		}
	} else if ($.isFunction(options)) {
		var successCallback = options;
		options = {};
		options.success = successCallback;
	}
	$.extend(options, { url: url, data: data, type: type, cache: false });
	if (!options.type) { options.type = "GET"; }
	var successCallback = options.success;
	options.success = function(data, status, request) {
		$("#alert-box").empty();
		if (successCallback) { successCallback(data, status, request); }
	}
	var _this = this;
	var errorCallback = options.error;
	options.error = function(request, status, e) {
		$("#alert-box").empty();
		var data = eval("(" + $.trim(request.responseText).replace(/\s+/g, " ") + ")");
		if (errorCallback) { errorCallback(data, request, status, e); } else { _this.error(data.message); }
	}
	this.info("请稍候...");
	$.ajax(options);
}
UI.prototype.get = function(url, data, options) { this.request(url, "GET", data, options); }
UI.prototype.post = function(url, data, options) { this.request(url, "POST", data, options); }
UI.prototype.put = function(url, data, options) {
	if (data && (!$.isEmptyObject(data))) {
		if (url.indexOf("?") < 0) { url += "?"; } else { url += "&"; }
		for (var key in data) { url += (key + "=" + data[key] + "&"); }
		url = url.replace(/&$/, "");
		this.request(encodeURI(url), "PUT", {}, options);
	} else {
		this.request(encodeURI(url), "PUT", data, options);
	}
}
UI.prototype.delete = function(url, data, options) { this.request(url, "DELETE", data, options); }

var ui = new UI();

Date.prototype.format = function(fmt) {
	function fmtStr(v) { return (v < 10) ? ("0" + v) : ("" + v); }
	return fmt.replace(/y+/, this.getFullYear())
		.replace(/M+/, fmtStr(this.getMonth() + 1))
		.replace(/d+/, fmtStr(this.getDate()))
		.replace(/H+/, fmtStr(this.getHours()))
		.replace(/m+/, fmtStr(this.getMinutes()))
		.replace(/s+/, fmtStr(this.getSeconds()));
}
