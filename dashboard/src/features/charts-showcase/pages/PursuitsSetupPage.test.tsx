import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import PursuitsSetupPage from "./PursuitsSetupPage";

describe("PursuitsSetupPage", () => {
  it("filters candidates by search and hides assigned rows by default", async () => {
    const user = userEvent.setup();

    render(<PursuitsSetupPage />);

    expect(screen.getByText("Top unassigned apps and websites in the last 30 days")).toBeInTheDocument();
    expect(screen.getByRole("row", { name: /VS Code.*program/i })).toBeInTheDocument();
    expect(screen.queryByRole("row", { name: /YouTube.*domain/i })).not.toBeInTheDocument();

    await user.type(screen.getByLabelText("Search candidates"), "docs");

    expect(screen.getByRole("row", { name: /Google Docs.*domain/i })).toBeInTheDocument();
    expect(screen.queryByRole("row", { name: /VS Code.*program/i })).not.toBeInTheDocument();
  });

  it("supports mixed program and domain selection with add preview", async () => {
    const user = userEvent.setup();

    render(<PursuitsSetupPage />);

    await user.click(within(screen.getByRole("row", { name: /VS Code.*program/i })).getByRole("checkbox"));
    await user.click(
      within(screen.getByRole("row", { name: /Google Docs.*domain/i })).getByRole("checkbox"),
    );
    await user.selectOptions(screen.getByLabelText("Assign to existing pursuit"), "Freelance Copywriting");

    expect(screen.getByText("2 selected")).toBeInTheDocument();
    expect(screen.getByText("Adds")).toBeInTheDocument();
    expect(screen.getByText("VS Code -> Freelance Copywriting")).toBeInTheDocument();
    expect(screen.getByText("Google Docs -> Freelance Copywriting")).toBeInTheDocument();
  });

  it("requires explicit confirmation before moving assigned items", async () => {
    const user = userEvent.setup();

    render(<PursuitsSetupPage />);

    await user.click(screen.getByLabelText("Show assigned"));
    await user.click(within(screen.getByRole("row", { name: /YouTube.*domain/i })).getByRole("checkbox"));
    await user.selectOptions(screen.getByLabelText("Assign to existing pursuit"), "Learning Japanese");

    expect(screen.getByText("Moves requiring confirmation")).toBeInTheDocument();
    expect(screen.getByText("YouTube: Entertainment -> Learning Japanese")).toBeInTheDocument();

    const applyButton = screen.getByRole("button", { name: "Apply changes" });
    expect(applyButton).toBeDisabled();

    await user.click(screen.getByLabelText("I understand selected assigned items will move pursuits"));

    expect(applyButton).toBeEnabled();
  });

  it("creates and edits pursuits with local state", async () => {
    const user = userEvent.setup();

    render(<PursuitsSetupPage />);

    await user.type(screen.getByLabelText("New pursuit name"), "Research");
    await user.selectOptions(screen.getByLabelText("New pursuit category"), "learning");
    await user.clear(screen.getByLabelText("New pursuit weekly goal"));
    await user.type(screen.getByLabelText("New pursuit weekly goal"), "6");
    await user.click(screen.getByRole("button", { name: "Create pursuit" }));

    expect(
      within(screen.getByLabelText("Pursuit to edit")).getByRole("option", { name: "Research" }),
    ).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Pursuit to edit"), "Research");
    await user.clear(screen.getByLabelText("Edit pursuit name"));
    await user.type(screen.getByLabelText("Edit pursuit name"), "Research Writing");

    expect(
      within(screen.getByLabelText("Pursuit to edit")).getByRole("option", {
        name: "Research Writing",
      }),
    ).toBeInTheDocument();
  });

  it("unassigns selected assigned rows with local state", async () => {
    const user = userEvent.setup();

    render(<PursuitsSetupPage />);

    await user.click(screen.getByLabelText("Show assigned"));
    await user.click(within(screen.getByRole("row", { name: /Bunpro.*domain/i })).getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Unassign selected" }));

    expect(screen.getByRole("row", { name: /Bunpro.*Unassigned/i })).toBeInTheDocument();
  });
});
