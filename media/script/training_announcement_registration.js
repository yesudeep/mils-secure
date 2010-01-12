jQuery(function(){
    var nomination_template = '<fieldset id="nomination_{0}"> \
          <legend>Nomination {0}</legend> \
          <label for="full_name_{0}"> \
            <span class="prefix">full name</span> \
            <input type="text" name="full_name_{0}" value="" class="required capitalize" /> \
            <span class="suffix"></span> \
          </label> \
          <label for="company_{0}"> \
            <span class="prefix">company</span> \
            <input type="text" name="company_{0}" value="" class="required capitalize" /> \
            <span class="suffix"></span> \
          </label> \
          <label for="designation_{0}"> \
            <span class="prefix">designation</span> \
            <input type="text" name="designation_{0}" value="" class="required capitalize" /> \
            <span class="suffix"></span> \
          </label> \
          <label for="email_{0}"> \
            <span class="prefix">email</span> \
            <input type="text" name="email_{0}" value="" class="required email" /> \
            <span class="suffix"></span> \
          </label> \
          <label for="phone_number_{0}"> \
            <span class="prefix">phone</span> \
            <input type="text" name="phone_number_{0}" value="" class="required phone" /> \
            <span class="suffix"><a href="#add_nomination">Add nomination</a></span> \
          </label> \
        </fieldset>',
        nominations_count = 1,
        training_announcement_key = jQuery("#form_training_registration").attr('key'),
        elements = {
            formTrainingRegistration: jQuery('#form_training_registration')
        };

    jQuery('#form_training_registration a[href="#add_nomination"]').live('click', function(event){
        event.preventDefault();
        event.stopPropagation();
        ++nominations_count;

        var elem = jQuery(this),
            html = jQuery.format(nomination_template, nominations_count),
            fieldset = elem.parents('fieldset');
        fieldset.after(html);
        jQuery('#form_training_registration input[name="name_' + nominations_count + '"]').focus();
        jQuery('#form_training_registration input[name="nominations_count"]').val(nominations_count);
        jQuery('#form_training_registration input[name="email_' + nominations_count + '"]').rules("add", {
            required: true,
            remote: {
                url: "/training_announcements/check_email_available/",
                type: "post",
                data: {
                    training_announcement_key: training_announcement_key,
                    index: nominations_count
                }
            },
            messages: {
                remote: "Please choose a new email address.  This one is already registered for this event."
            }
        });
        return false;
    });


    /*jQuery('#form_training_registration input[name="email_' + nominations_count + '"]').rules("add", {
        required: true,
        remote: {
            url: "/training_announcements/check_email_available/",
            type: "post",
            data: {
                training_announcement_key: training_announcement_key,
                index: nominations_count
            }
        },
        messages: {
            remote: "Please choose a new email address.  This one is already registered for this event."
        }
    });*/
    elements.formTrainingRegistration.validate();
});

