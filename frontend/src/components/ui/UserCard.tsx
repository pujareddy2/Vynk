import Avatar from "../ui/Avatar";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import Card from "../ui/Card";

interface UserCardProps {
  name: string;
  username?: string;
  bio?: string;
  imageUrl?: string;
  interests?: string[];
  actionLabel?: string;
  onAction?: () => void;
}

export default function UserCard({
  name,
  username,
  bio,
  imageUrl,
  interests = [],
  actionLabel = "View profile",
  onAction,
}: UserCardProps) {
  return (
    <Card>
      <div className="flex items-start gap-4">
        <Avatar
          name={name}
          imageUrl={imageUrl}
          size="lg"
        />

        <div className="min-w-0 flex-1">
          <h3 className="truncate text-lg font-bold text-slate-900 dark:text-white">
            {name}
          </h3>

          {username && (
            <p className="mt-1 truncate text-sm text-slate-500 dark:text-slate-400">
              @{username}
            </p>
          )}
        </div>
      </div>

      {bio && (
        <p className="mt-4 text-sm leading-6 text-slate-500 dark:text-slate-400">
          {bio}
        </p>
      )}

      {interests.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {interests.slice(0, 4).map((interest) => (
            <Badge key={interest} variant="teal">
              {interest}
            </Badge>
          ))}
        </div>
      )}

      {onAction && (
        <Button
          type="button"
          variant="outline"
          onClick={onAction}
          className="mt-5 w-full"
        >
          {actionLabel}
        </Button>
      )}
    </Card>
  );
}