openerp.web_widget_vote = function(instance) {

instance.web.form.VoteBase = instance.web.form.FieldChar.extend({
    template: 'VoteBase',

    render_value: function() {
        var vote = new instance.web.form.VoteFiveStar(this, this.get('value'));
        $('#VoteBase').empty();
        vote.appendTo(this.$el);
        this._super();
    },

});


instance.web.form.VoteFiveStar = instance.web.Widget.extend({
    template: 'VoteFiveStar',

    init: function (parent, votes) {
        this._super(parent) ;
        this.votes = votes;
        this.parent = parent;
    },

    start: function () {
        this._super();

        object = this
        var model = new instance.web.Model(this.parent.view.dataset.model);

//TODO Try to search for the form mode in variable, this condition isn't reliable because it only work the first time.
//TODO http://help.openerp.com/question/47064/how-to-know-in-javascript-the-state-of-a-form-editview-mode/
        if ($('.oe_formview').hasClass('oe_form_editable')) {
            this.$('.star_vote_five_star').addClass('listener_set').each(function () {
                $(this).hover(function() {
                    object.update_stars($(this).attr('name'),$(this).attr('value'));
                }, function() {
                    object.update_stars($(this).attr('name'),$(this).parent().attr('value'));
                });
                $(this).click(function() {
//TODO Try to update this.('value') instead
                    model.call("write",[[object.parent.view.datarecord.id], {'vote_vote': [{'type_id': $(this).attr('name'), 'value': $(this).attr('value')}]}], {context: new instance.web.CompoundContext()}).then(function(result) {
                        $('.ok_vote_five_star[name="' + $(this).attr('name') + '"]').hide();
                        $('.ok_vote_five_star[name="' + $(this).attr('name') + '"]').fadeIn();
                    });
                    $(this).parent().attr('value', $(this).attr('value'));
                });
            });

            this.$('#VoteFiveStarClear').addClass('listener_set').each(function () {
                $(this).show();
                $(this).click(function() {
                    model.call("clear_votes",[[object.parent.view.datarecord.id]], {context: new instance.web.CompoundContext()}).then(function(result) {
                        $('.star_vote_five_star').removeClass('oe_star_on').addClass('oe_star_off');
                    });
                    $('.oe_form_field_vote_five_star').attr('value', -3);
                });

            });
        }


        for (index = 0; index < this.votes.length; ++index) {
            var vote = this.votes[index];
            this.update_stars(vote['id'], vote['value']);
        }
    },

    update_stars: function(id, value) {
        if (value == false) {
            value = 0;
        }
        this.$('.star_vote_five_star[name="' + id + '"]').removeClass('oe_star_on').addClass('oe_star_off')
        i = -2
        while (i <= value) {
            this.$('.star_vote_five_star[name="' + id + '"][value="' + i + '"]').removeClass('oe_star_off').addClass('oe_star_on')
            i += 1
        }
    },


});

instance.web.form.widgets = instance.web.form.widgets.extend({
    'vote_five_star' : 'instance.web.form.VoteBase',
});

};
