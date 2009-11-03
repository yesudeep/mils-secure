// common.js should be included before this file.

function createItemHTML(user){
    return dataListEntry(user, user.nickname, defaultActions('users', user), defaultTags());
}

function editItem(){

}

jQuery(function(){
    jQuery.getJSON('/api/users/list', {}, function(users){
        var user, html = [];
        for (var i = 0, len = users.length; i < len; ++i){
            user = users[i];
            html.push(createItemHTML(user));
        }
        jQuery('#data-list').html(html.join(''));
    });
});

