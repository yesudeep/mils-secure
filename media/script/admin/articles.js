// common.js should be included before this file.

function createItemHTML(article){
    return dataListEntry(article, article.title + ' (' + article.section_type + ')', defaultActions('articles', article), defaultTags());
}

function editItem(){

}

jQuery(function(){
    jQuery.getJSON('/api/articles/list/', {}, function(articles){
        var article = {};
        var html = [];
        for (var i = 0, len = articles.length; i < len; ++i){
            article = articles[i];
            html.push(createItemHTML(article));
        }
        jQuery('#data-list').html(html.join(''));
    });

    jQuery('input[name="title"]').live('keyup', function(event){
        var elem = jQuery(this),
            form = elem.parents('form'),
            buddyInput = jQuery('input[name="slug_title"]', form),
            buddyUrlSlug = jQuery('.url_slug', form),
            slug = slugify(elem.val());
        buddyInput.val(slug);
        buddyUrlSlug.html(slug);
    });
});

