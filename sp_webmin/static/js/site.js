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
function post_data(url, data, selector) {
    $.post(url, data, function(data) {
        console.log(data);
        selector.append($(data["row"]));
    }, "json");
    return false;
}
function insertNewSettingsRow() {
    $("<tr><td><input type=\"text\" class=\"input-sm\" autocomplete=\"off\"\
           onkeyup=\"$(this).parent().parent().find('.settingValue').\
           attr('name', $(this).val())\"></td>\
            <td><input type=\"text\" class=\"input-sm settingValue\" autocomplete=\"off\"\
           size=\"128\" maxlength=\"128\"></td>\
            <td><button class=\"btn btn-primary btn-sm\"\
                        onclick=\"$(this).parent().parent().remove()\">Remove</button></td></tr>").insertBefore("#end");
}
function checkSteamID(url, steamID, finish) {
    return $.get(url, {steamID: steamID}, function(data) {
            return finish(data["result"], data["player"])
        }, "json")
}
function validateSteamIDField(url) {
    var playerInput = $('#inputPlayer');
    return checkSteamID(url, playerInput.val(), function(result, player) {
            var label = $('#name');
            var input = $('#inputName');
            if(result) {
                playerInput.toggleClass('badInput', false);
                playerInput.toggleClass('goodInput', true);
                label.find('span').text(player['name']);
                input.val(player['name']);
            } else {
                playerInput.toggleClass('badInput', true);
                playerInput.toggleClass('goodInput', false);
                label.find('span').text('');
                input.val('');
            }
        });
}
var multipliers = {
        'Seconds': 1,
        'Minutes': 60,
        'Hours': 3600,
        'Days': 86400,
        'Weeks': 604800,
        'Months': 2592000,
        'Years': 31104000
    };
function calculateDurationInSeconds(duration, unit) {
    return duration * multipliers[unit];
}




