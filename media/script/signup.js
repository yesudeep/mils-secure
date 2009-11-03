(function($){
    $(function(){
        var phone_number_count = 1;
        var phone_types_html = $('#phone_types').html();
        var phone_number_field_html = [
            '<label id="field_phone_number_{0}" class="column" for="phone_number_{0}">',
            '<span class="prefix">phone number</span>',
            '<input type="text" name="phone_number_{0}" value="" />',
            '<select name="phone_type_{0}">{1}</select>',
            '<span class="suffix"><a href="#add_phone_number">add another</a></span>',
            '</label>'].join('');

        $('#form_signup a[href="#add_phone_number"]').live('click', function(e){
           var target = $(this);
           ++phone_number_count;
           html = $.format(phone_number_field_html, phone_number_count, phone_types_html);
           target.parent().parent().parent().append(html);
           $('#form_signup input[name="phone_number_count"]').val(phone_number_count);
        });

        var $field_first_name = $('#form_signup input[name="first_name"]');
        var $field_last_name = $('#form_signup input[name="last_name"]');
        var $field_email_address = $('#form_signup input[name="email_address"]');
        var $field_company = $('#form_signup input[name="company"]');
        var $field_corporate_email_address = $('#form_signup input[name="corporate_email_address"]');
        var $field_city = $('#form_signup input[name="city"]');
        var $field_state_province = $('#form_signup input[name="state_province"]');
        var $field_landmark = $('#form_signup input[name="landmark"]');
        var $field_designation = $('#form_signup input[name="designation"]');
        var $field_apartment = $('#form_signup input[name="apartment"]');
        var $field_street_name = $('#form_signup input[name="street_name"]');
        var $field_phone_number = $('#form_signup input[name="phone_number_1"]');
        var $field_graduation_year = $('#form_signup select[name="graduation_year"]');
        var $field_t_shirt_size = $('#form_signup select[name="t_shirt_size"]');
        var $field_is_student = $('#form_signup input[name="is_student"]');


        $field_is_student.change(function(e){
            var elem = $(this);
            $field_company.val('MILS');
            $field_designation.val('Student');
        });
        var email_field_value = $.trim($field_email_address.val());
        function set_field_if_empty(field, value){
            if ($.trim(field.val()) === '' && value){
                field.val(value);
            }
        }
        function fill_form(user_info, override){
           if (override){
               $field_first_name.val(user_info.first_name);
               $field_last_name.val(user_info.last_name);
               $field_designation.val(user_info.designation);
               $field_company.val(user_info.company);
               $field_phone_number.val(user_info.phone_number);
           } else {
               set_field_if_empty($field_first_name, user_info.first_name);
               set_field_if_empty($field_last_name, user_info.last_name);
               set_field_if_empty($field_designation, user_info.desigation);
               set_field_if_empty($field_company, user_info.company);
               set_field_if_empty($field_phone_number, user_info.phone_number);
           }
           if (user_info.graduation_year){
               $field_graduation_year.val(user_info.graduation_year);
           }
           if (user_info.t_shirt_size){
               $field_t_shirt_size.val(user_info.t_shirt_size);
           }
        }

        function on_email_change(e){
            var email_address = $.trim($field_email_address.val());
            var corporate_email_address = $.trim($field_corporate_email_address.val());

            $field_email_address.val(email_address);
            $field_corporate_email_address.val(corporate_email_address);

            $.getJSON('/json/existing_user/', {
                'email_address': email_address,
                'corporate_email_address': corporate_email_address
            }, function(user, textStatus){
                if (textStatus == 'success' && user.graduation_year){
                    fill_form(user, email_field_value === '');
                }
            });
        }
        /*$('#form_signup').validate({
            rules: {
                first_name: 'required',
                last_name: 'required',
                company: 'required',
                designation: 'required',
                phone_number_1: 'required',
                apartment: 'required',
                street_name: 'required',
                landmark: 'required',
                city: 'required',
                state_province: 'required',
                zip_code: 'required',
                email_address: {
                    required: true,
                    email: true
                },
                corporate_email_address: {
                    email: true
                }
            }
        });*/
        $('#form_signup input').blur(function(e){
            $(this).valid();
        });

        $field_email_address.focus();

        /*
        .change(on_email_change).change();

        $field_corporate_email_address.change(on_email_change);
        $field_first_name.change(fn_sanitize).change();
        $field_last_name.change(fn_sanitize).change();
        $field_city.change(fn_sanitize).change();
        $field_state_province.change(fn_sanitize).change();
        $field_landmark.change(fn_sanitize).change();
        $field_designation.change(fn_sanitize).change();
        $field_apartment.change(fn_sanitize).change();
        $field_street_name.change(fn_sanitize).change();*/

        $field_phone_number.change(function(e){
            var o = $(this);
            o.val($.trim(o.val()));
        }).change();
        /*
        function fn_sanitize(e){
           var o = $(this);
           o.val($.trim(o.val()));
           o.val(sanitize_capitalization(o.val()));
        }
        function sanitize_capitalization(value){
           if(value && is_same_case_string(value)){
               return titleCaps(value.toLowerCase());
           } else {
               return value;
           }
        }
        function is_upper_case_string(string){
           return !!string.match(/^[^a-z]*$/);
        }
        function is_lower_case_string(string){
           return !!string.match(/^[^A-Z]*$/);
        }
        function is_same_case_string(string){
           return (is_lower_case_string(string) || is_upper_case_string(string));
        }*/
    });
})(jQuery);

