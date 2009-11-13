// common.js should be included before this file.

function createItemHTML(sponsor){
    return dataListEntry(sponsor, sponsor.subject + ((sponsor.when_sent)? ' (' + sponsor.when_sent + ')': ''), defaultActions('sponsors', sponsor), defaultTags());
}

function editItem(){

}

jQuery(function(){
    jQuery.getJSON('/api/sponsors/list/', {}, function(sponsors){
        var sponsor = {};
        var html = [];
        for (var i = 0, len = sponsors.length; i < len; ++i){
            sponsor = sponsors[i];
            html.push(createItemHTML(sponsor));
        }
        jQuery('#data-list').html(html.join(''));
    });
});

