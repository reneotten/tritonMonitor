from pywebpush import webpush, WebPushException
import json
import os


def trigger_push_notification(push_subscription, title, body):
    try:
        response = webpush(
            subscription_info=json.loads(push_subscription.subscription_json),
            data=json.dumps({"title": title, "body": body}),
            vapid_private_key=os.environ["VAPID_PRIVATE_KEY"],
            vapid_claims={
                "sub": "mailto:{}".format(
                    os.environ["VAPID_CLAIM_EMAIL"])
            }
        )
        return response.ok
    except WebPushException as ex:
        if ex.response and ex.response.json():
            extra = ex.response.json()
            print("Remote service replied with a {}:{}, {}",
                  extra.code,
                  extra.errno,
                  extra.message
                  )
        return False


def trigger_push_notifications_for_subscriptions(subscriptions, title, body):
    return [trigger_push_notification(subscription, title, body)
            for subscription in subscriptions]


def trigger_push_notifications_for_user(user, title, body):
    return [
        trigger_push_notification(subscription, title, body)
        for subscription in user.push_subscriptions]


def trigger_push_notifications_for_users(users, title, body, contents=None):
    return { user.id: trigger_push_notifications_for_user(user, title, body) for user in users}