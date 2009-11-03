// common.js should be included before this file.

function announcementActions(announcement){
    return defaultActions('announcements', announcement); /* + '<a class="awesome-button" rel="cancel-announcement" href="/api/announcements/' + announcement.key + '/cancel"><span class="symbol">&times;</span> Cancel announcement</a>'*/;
}

function createItemHTML(announcement){
    return dataListEntry(announcement, ((announcement.is_canceled)? '[CANCELED] ': '') + announcement.title + ' (total registrants: ' + (announcement.total_participant_count || 0) + '; active registrants: ' + (announcement.participant_count || 0) + ')', announcementActions(announcement), defaultTags());
}

var calendarOptions = {
    timePeriod: 15,
    showTime: true,
    format: "%Y-%m-%dT%H:%M:%S",
    fxDuration: 1
};

function editItem(){
    new Calendar(calendarOptions).assignTo('edit-when-from');
    new Calendar(calendarOptions).assignTo('edit-when-to');
    new Calendar(calendarOptions).assignTo('edit-when-registration-ends');
    new Calendar(calendarOptions).assignTo('edit-when-payment-is-calculated');
}

jQuery(function(){
    jQuery.getJSON('/api/announcements/list/', {}, function(announcements){
        var announcement = {}, html = [];
        for (var i = 0, len = announcements.length; i < len; ++i){
            announcement = announcements[i];
            html.push(createItemHTML(announcement));
        }
        jQuery('#data-list').html(html.join(''));
    });

    jQuery('form.new input[name="brochure_url"], form.edit input[name="brochure_url"]').live('change', function(e){
        var elem = jQuery(this),
            form = elem.parents('form'),
            img = jQuery('img.preview', form),
            link = jQuery('a.preview_url', form);
        img.attr('src', elem.val());
        link.attr('href', elem.val());
    });


    /*jQuery('a[rel="view-registrants"]').live('click', function(e){
        e.stopPropagation();
        e.preventDefault();

        var item = jQuery(this),
            url = item.attr('href');

        jQuery.get(url, {}, function(data, textStatus){
            console.log(data);
        });

        return false;
    });*/

    jQuery('a[rel="approve-payment"]').live('click', function(event){
        event.preventDefault();
        event.stopPropagation();

        var item = jQuery(this),
            li = item.parents('li.data-item'),
            url = item.attr('href');

        showPromptDialog({
            title: 'Confirm payment from this registrant?',
            message: "Confirming payment means the registrant must now attend.",
            subMessage: 'A confirmatory email message will be sent to the registrant on your approval.',
            yesLabel: '&#10004; Yes, confirm',
            noLabel: '&times; No, please cancel',
            hideCancelButton: true,
            onYesClicked: function(){
                jQuery.get(url, {}, function(data, textStatus){
                    li.addClass('approved-payment');
                });
            }
        });
        return false;
    });
/*
    jQuery('a[rel="cancel-announcement"]').live('click', function(event){
        event.stopPropagation();
        event.preventDefault();

        var item = jQuery(this),
            h1 = item.parent().parent(),
            url = item.attr('href');

        showPromptDialog({
            title: 'Cancel this announcement?',
            message: "You will not be able to recover this announcement once you cancel the announcement.",
            subMessage: 'Emails will be sent to registered participant about the cancelation.',
            yesLabel: '&#10004; Yes, cancel announcement',
            noLabel: "&times; No, don't cancel announcement",
            hideCancelButton: true,
            onYesClicked: function(){
                jQuery.get(url, function(data, textStatus){
                    h1.addClass('canceled');
                });
            }
        });

        return false;
    });
*/

    jQuery('a[rel="new"]').die('click', newItemClicked).live('click', function(e){
        e.stopPropagation();
        e.preventDefault();

        var item = jQuery(this),
            url = item.attr('href');

        jQuery.get(url, {}, function(data, textStatus){
            jQuery('#new-item').html(data);

            new Calendar(calendarOptions).assignTo('new-when-from');
            new Calendar(calendarOptions).assignTo('new-when-to');
            new Calendar(calendarOptions).assignTo('new-when-registration-ends');
            new Calendar(calendarOptions).assignTo('new-when-payment-is-calculated');
        });

        return false;
    });

});

