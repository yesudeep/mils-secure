// common.js should be included before this file.

function defaultActions(type, item){
    return '<a class="star ' + ((item.is_starred)? 'on': '') + '" href="/api/' + type + '/' + item.key + '/toggle_star/"></a>\
    <a class="awesome-button cool" rel="approve" href="/api/' + type + '/' + item.key + '/approve/"><span class="symbol">&#10004;</span> Approve</a>\
    <a class="awesome-button warm" rel="unapprove" href="/api/' + type + '/' + item.key + '/unapprove/"><span class="symbol">&#10004;</span> Unapprove</a>\
    <a class="awesome-button" rel="edit" href="/api/' + type + '/' + item.key + '/edit/"><span class="symbol">&minus;</span> Edit Profile</a>\
    <a class="awesome-button" rel="delete" href="/api/' + type + '/' + item.key + '/delete/"><span class="symbol">&times;</span> Delete</a>\
    <a class="awesome-button" rel="undelete" href="/api/' + type + '/' + item.key + '/undelete/"><span class="symbol">&times;</span> Undelete</a>';
}

function createItemHTML(user){
    return dataListEntry(user, user.nickname + ' (' + user.auth_provider + ')', defaultActions('users', user), defaultTags());
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

