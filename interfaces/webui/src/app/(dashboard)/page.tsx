import * as React from "react";
import { Card } from "@/components/ui/card";

function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Welcome to ETHAN Cognitive Runtime
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <div className="p-6">
            <div className="text-sm font-medium text-muted-foreground">
              Active Agents
            </div>
            <div className="text-3xl font-bold mt-2">12</div>
            <div className="text-xs text-green-500 mt-1">+2 from last hour</div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="text-sm font-medium text-muted-foreground">
              Goals Completed
            </div>
            <div className="text-3xl font-bold mt-2">48</div>
            <div className="text-xs text-green-500 mt-1">+12 today</div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="text-sm font-medium text-muted-foreground">
              Memory Entries
            </div>
            <div className="text-3xl font-bold mt-2">1.2K</div>
            <div className="text-xs text-muted-foreground mt-1">Last 24 hours</div>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="text-sm font-medium text-muted-foreground">
              System Health
            </div>
            <div className="text-3xl font-bold mt-2 text-green-500">98%</div>
            <div className="text-xs text-muted-foreground mt-1">All systems operational</div>
          </div>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
          <div className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="h-2 w-2 rounded-full bg-green-500 mt-2" />
              <div className="flex-1">
                <p className="text-sm">Agent "CodeReviewer" completed task</p>
                <p className="text-xs text-muted-foreground mt-1">2 minutes ago</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="h-2 w-2 rounded-full bg-blue-500 mt-2" />
              <div className="flex-1">
                <p className="text-sm">New goal created: "Deploy to production"</p>
                <p className="text-xs text-muted-foreground mt-1">15 minutes ago</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="h-2 w-2 rounded-full bg-purple-500 mt-2" />
              <div className="flex-1">
                <p className="text-sm">Memory entry stored: user preference</p>
                <p className="text-xs text-muted-foreground mt-1">1 hour ago</p>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

export default DashboardPage;