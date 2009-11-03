/**
 * Creates a slugified string
 */
function slugify(string){
    return string.toLowerCase().replace(/\s+/g,'-').replace(/[^a-zA-Z0-9\-]/g,'');
}

function dataListEntry(item, title, actions, tags){
    var html = ['<li id="', item.key, '" class="item"><h1 class="',
        ((item.is_deleted)? 'deleted': ''), ' ',
        ((item.is_active)? '': 'unapproved'), ' ',
        ((item.is_starred)? 'starred': ''), ' ',
        ((item.is_canceled)? 'canceled': ''),
        '"><span class="title">', title, '</span><span class="tags">',
        tags, '</span><span class="actions">', actions,
        '</span></h1><div id="', item.key, '-info" class="info"></div></li>'];
    return html.join('');
}

function defaultTags(){
    return '<a href="#starred">important</a><a href="#unapproved">not approved</a>';
}

function defaultActions(type, item){
    return '<a class="star ' + ((item.is_starred)? 'on': '') + '" href="/api/' + type + '/' + item.key + '/toggle_star/"></a>\
    <a class="awesome-button cool" rel="approve" href="/api/' + type + '/' + item.key + '/approve/"><span class="symbol">&#10004;</span> Approve</a>\
    <a class="awesome-button warm" rel="unapprove" href="/api/' + type + '/' + item.key + '/unapprove/"><span class="symbol">&#10004;</span> Unapprove</a>\
    <a class="awesome-button" rel="edit" href="/api/' + type + '/' + item.key + '/edit/"><span class="symbol">&minus;</span> Edit</a>\
    <a class="awesome-button" rel="delete" href="/api/' + type + '/' + item.key + '/delete/"><span class="symbol">&times;</span> Delete</a>\
    <a class="awesome-button" rel="undelete" href="/api/' + type + '/' + item.key + '/undelete/"><span class="symbol">&times;</span> Undelete</a>';
}

function showPromptDialog(options) {
    options = options || {};
    options.title = options.title || 'Untitled';
    options.message = options.message || "No message available.";
    options.subMessage = options.subMessage || "No message available.";
    options.onNoClicked = options.onNoClicked || function(){};
    options.onYesClicked = options.onYesClicked || function(){};
    options.onCancelClicked = options.onCancelClicked || function(){};
    options.width = options.width || "550px";
    options.yesLabel = options.yesLabel || '<span class="symbol">&#10004;</span> Yes';
    options.cancelLabel = options.cancelLabel || "Cancel";
    options.noLabel = options.noLabel || '<span class="symbol">&times;</span> No';

    var randId = Math.floor(Math.random() * 27644437 + 1);
    var box = new Lightbox({showCloseButton: false, fxDuration: 100});
    var content = '<p>' + options.message + '</p><p class="small">' +
        options.subMessage + '</p><div class="actions">';
    if (!options.hideCancelButton){
        content += '<button type="button" id="cancel-' + randId + '">' + options.cancelLabel + '</button>'
    }
    if (!options.hideNoButton){
        content += '<button type="button" id="no-' + randId + '">' + options.noLabel + '</button>';
    }
    if (!options.hideYesButton){
        content += '<button type="button" id="yes-' + randId + '">' + options.yesLabel + '</button>';
    }
    content += '</div>';

    box.setTitle(options.title);
    box.show(content, {width: options.width});

    jQuery('#yes-' + randId).live('click', function(e){
        box.hide();
        options.onYesClicked();
    });
    jQuery('#no-' + randId).live('click', function(e){
        box.hide();
        options.onNoClicked();
    });
    jQuery('#cancel-' + randId).live('click', function(e){
        box.hide();
        options.onCancelClicked();
    });
}

function newItemClicked(event){
    event.preventDefault();

    var item = jQuery(this),
        url = item.attr('href');

    jQuery.get(url, {}, function(data, textStatus){
        jQuery('#new-item').html(data);
    });
}


jQuery(function(){


    var elements = {
        dataList: jQuery('ul.data-list'),
        star: jQuery('a.star'),
        newItem: jQuery('#new-item')
    }


    // Accordion behavior (click).
    jQuery('> li > h1', elements.dataList).live('click', function(e){
        var item = jQuery(this).parent('li');
        item.siblings('.active').removeClass('active');
        item.toggleClass('active');
        var id = item.attr('id'),
            info = jQuery('#' + id + '-info');

        if (item.hasClass('active')){
            var edit_link = jQuery('a[rel="edit"]', item),
                url = edit_link.attr("href");
            jQuery.get(url, {}, function(data, textStatus){
                info.html(data);
                editItem();
                jQuery('form.edit').validate();
            });
        }
    });


    jQuery('a[rel="unapprove"]').live('click', function(event){
        event.stopPropagation();
        event.preventDefault();

        var elem = jQuery(this),
            h1 = elem.parent().parent(),
            url = elem.attr('href');

        showPromptDialog({
            title: 'Unapprove (disable) this record?',
            message: "Unapproving will hide previously public information and will disable this record.",
            subMessage: 'If this is a user you are unapproving she may not be able to log in until you approve her again. Published articles will be removed from public visibility.',
            yesLabel: '&#10004; Yes, unapprove',
            noLabel: '&times; No, please cancel',
            hideCancelButton: true,
            onYesClicked: function(){
                jQuery.get(url, {}, function(data, textStatus){
                    h1.addClass('unapproved');
                });
            }
        });

        return false;
    });
    jQuery('a[rel="approve"]').live('click', function(event){
        event.stopPropagation();
        event.preventDefault();

        var elem = jQuery(this),
            h1 = elem.parent().parent(),
            url = elem.attr('href');

        showPromptDialog({
            title: 'Approve (enable) this record?',
            message: "Approving will publish information publically and may also send email.",
            subMessage: 'If this is a user you are approving an activation email will be sent to her. Articles will be published.',
            yesLabel: '&#10004; Yes, approve',
            noLabel: '&times; No, please cancel',
            hideCancelButton: true,
            onYesClicked: function(){
                jQuery.get(url, {}, function(data, textStatus){
                    h1.removeClass('unapproved');
                });
            }
        });

        return false;
    });
    jQuery('.sub-data-list a[rel="unapprove"]').live('click', function(event){
        event.stopPropagation();
        event.preventDefault();

        var elem = jQuery(this),
            li = elem.parents('li.data-item'),
            url = elem.attr('href');

        showPromptDialog({
            title: 'Unapprove (disable) this record?',
            message: "Unapproving will hide previously public information and will disable this record.",
            subMessage: 'If this is a user you are unapproving she may not be able to log in until you approve her again. Published articles will be removed from public visibility.',
            yesLabel: '&#10004; Yes, unapprove',
            noLabel: '&times; No, please cancel',
            hideCancelButton: true,
            onYesClicked: function(){
                jQuery.get(url, {}, function(data, textStatus){
                    li.addClass('unapproved');
                });
            }
        });

        return false;
    });
    jQuery('.sub-data-list a[rel="approve"]').live('click', function(event){
        event.stopPropagation();
        event.preventDefault();

        var elem = jQuery(this),
            li = elem.parents('li.data-item'),
            url = elem.attr('href');

        showPromptDialog({
            title: 'Approve (enable) this record?',
            message: "Approving will publish information publically and may also send email.",
            subMessage: 'If this is a user you are approving an activation email will be sent to her. Articles will be published.',
            yesLabel: '&#10004; Yes, approve',
            noLabel: '&times; No, please cancel',
            hideCancelButton: true,
            onYesClicked: function(){
                jQuery.get(url, {}, function(data, textStatus){
                    li.removeClass('unapproved');
                });
            }
        });

        return false;
    });

    jQuery('form.edit').live('submit', function(e){
        var form = jQuery(this),
        action = form.attr('action'),
        method = form.attr('method'),
        formData = form.serialize(),
        item = form.parents('li.item');

        jQuery.ajax({
            type: method.toUpperCase(),
            url: action,
            data: formData,
            dataType: "json",
            success:function(data){
                // Update the datalist.
                // The createItemHTML function is defined in corresponding model.js files.
                item.replaceWith(createItemHTML(data));
            }
        });

        return false;
    });
    jQuery('form.new').live('submit', function(e){
        var form = jQuery(this),
        action = form.attr('action'),
        method = form.attr('method'),
        formData = form.serialize();

        jQuery.ajax({
            type: method.toUpperCase(),
            url: action,
            data: formData,
            dataType: "json",
            success:function(data){
                // Add to the datalist.
                // The createItemHTML function is defined in corresponding model.js files.
                elements.dataList.prepend(createItemHTML(data));
                jQuery('#new-item').html("");
                jQuery('form.new').validate();
            }
        });

        return false;
    });
    jQuery('a[rel="new"]').live('click', newItemClicked);
    jQuery('a[rel="edit"]').live('click', function(event){
        // The accordion will display the form/information.
        // However, we don't want this link to change the page location.
        event.preventDefault();
    });
    /*jQuery('input[name="filter"]').liveFilter('ul.data-list', {
        onComplete: function(){
            console.log("filtered");
        },
        timeout: 100,
        includeHTML: true,
        childSelector: 'li > span.title'
    });*/
    jQuery('a.star').live('click', function(event){
        event.stopPropagation();
        event.preventDefault();

        var elem = jQuery(this),
            h1 = elem.parent().parent(),
            url = elem.attr("href");

        jQuery.get(url, {}, function(data, textStatus){
            if (data){
                elem.addClass("on");
                h1.addClass('starred');
            } else {
                elem.removeClass("on");
                h1.removeClass('starred');
            }
        });

        return false;
    });
    jQuery('a[rel="undelete"]').live('click', function(event){
        event.stopPropagation();
        event.preventDefault();

        var elem = jQuery(this),
            //delete_button = elem.siblings('a[rel="delete"]'),
            h1 = elem.parent().parent(),
            url = elem.attr('href');

        jQuery.get(url, {}, function(data, textStatus){
            h1.removeClass('deleted');
        });

        return false;
    });
    jQuery('a[rel="delete"]').live('click', function(event){
        event.stopPropagation();
        event.preventDefault();

        var elem = jQuery(this),
            //undelete = elem.siblings('a[rel="undelete"]'),
            h1 = elem.parent().parent(),
            url = elem.attr('href');

        showPromptDialog({
            title: 'Delete this record?',
            message: "Are you sure you want to delete this record?",
            subMessage: 'Deleted records can be recovered since they are never permanently deleted, only marked such.',
            yesLabel: '&#10004; Yes, delete record',
            noLabel: '&times; No, keep record',
            hideCancelButton: true,
            onYesClicked: function(){
                jQuery.get(url, {}, function(data, textStatus){
                    h1.addClass('deleted');
                });
            }
        });

        return false;
    });
});

