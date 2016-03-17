function add_server(url, name, selector) {
    $.post(url, {name: name}, function(data) {
        selector
         .append($("<option/>")
         .val(data["id"])
         .text(data["name"] + " (" + data["id"] + ")"));
    }, "json");
    return false;
}

function add_object(url, identifier, type, selector) {
    $.post(url, {identifier: identifier, type: type}, function(data) {
        var tr = $("<tr>" +
            "<td><a href='" + data["url"] + "'>" + data["name"] + "</a></td>" +
            "<td><a href='" + data["steamUrl"] + "'>" +
            data["identifier"] + "</a></td></tr>");
        selector.append(tr);
    }, "json");
    return false;
}