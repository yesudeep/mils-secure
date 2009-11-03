// common.js should be included before this file.


function mailActions(type, item){
    return '<a class="star ' + ((item.is_starred)? 'on': '') + '" href="/api/' + type + '/' + item.key + '/toggle_star/"></a>\
    <a class="awesome-button cool" rel="approve" href="/api/' + type + '/' + item.key + '/approve/"><span class="symbol">&#10004;</span> Approve</a>\
    <a class="awesome-button" rel="edit" href="/api/' + type + '/' + item.key + '/edit/"><span class="symbol">&minus;</span> Edit</a>\
    <a class="awesome-button" rel="delete" href="/api/' + type + '/' + item.key + '/delete/"><span class="symbol">&times;</span> Delete</a>\
    <a class="awesome-button" rel="undelete" href="/api/' + type + '/' + item.key + '/undelete/"><span class="symbol">&times;</span> Undelete</a>';
}

function createItemHTML(mail){
    return dataListEntry(mail, mail.subject + ((mail.when_sent)? ' (' + mail.when_sent + ')': ''), mailActions('mails', mail), defaultTags());
}

function editItem(){

}

jQuery(function(){
    jQuery.getJSON('/api/mails/list/', {}, function(mails){
        var mail = {};
        var html = [];
        for (var i = 0, len = mails.length; i < len; ++i){
            mail = mails[i];
            html.push(createItemHTML(mail));
        }
        jQuery('#data-list').html(html.join(''));
    });
});

